%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% AGENTE LOGICO - Pitfall!
%%
%% Divisao de trabalho: o Prolog (este arquivo) so INFERE e DECIDE O QUE
%% QUER (objetivos). O caminho ate o objetivo e planejado em Python
%% (planejador.py, A*), apenas sobre as casas que o Prolog inferiu seguras.
%%
%% Regra de ouro: as regras de decisao abaixo NUNCA consultam tile/3
%% (mapa real). Elas usam apenas:
%%   - percepcao_vista/3 : o que o agente percebeu em cada casa visitada
%%   - bloqueada/2, tele/2 : perigos que o agente descobriu na pratica
%%   - u_visto/2 : casas onde o agente percebeu "reflexo" (item de energia)
%% A unica ponte com o ambiente sao os sensores (sensor_local/1 e
%% observacoes/1 do main.pl), que simulam brilho/reflexo/brisa/passos/palmas.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

:- dynamic percepcao_vista/3.   % percepcao_vista(X,Y,ListaDePercepcoesAdjacentes)
:- dynamic bloqueada/2.         % casa onde o agente tomou dano (inimigo)
:- dynamic tele/2.              % casa que teletransportou o agente
:- dynamic u_visto/2.           % item de energia visto e ainda nao pego
:- dynamic energia_ant/1.
:- dynamic intencao/2.          % destino do ultimo "andar"
:- dynamic limite_risco/1.
:- dynamic ouro_coletado/1.     % quantos ouros o agente ja pegou

% total de ouros do labirinto (dado do enunciado)
total_ouro(3).

% Risco maximo aceito ao explorar casa nao provada segura
% (pocos pesam 1000*probabilidade). 100 aceita casas com poco pouco provavel
% (~6%) mas recusa casas com ~1/3 ou mais de chance de poco.
limite_risco(100).

% probabilidade a priori de cada perigo (8 pocos, 4 inimigos, 4 teletransp. em 144)
prior(brisa, 0.06).
prior(passos, 0.03).
prior(palmas, 0.03).

peso_risco(brisa, 1000).   % poco: morte
peso_risco(passos, 150).   % inimigo: dano pesado (varias acoes sobre a casa)
peso_risco(palmas, 20).    % teletransporte: aleatorio

reset_agente :-
    retractall(percepcao_vista(_,_,_)),
    retractall(bloqueada(_,_)),
    retractall(tele(_,_)),
    retractall(u_visto(_,_)),
    retractall(energia_ant(_)),
    retractall(intencao(_,_)),
    retractall(ouro_coletado(_)),
    assertz(ouro_coletado(0)).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Geometria
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

dentro(X,Y) :- map_size(MX,MY), X >= 1, Y >= 1, X =< MX, Y =< MY.

viz(X,Y,NX,Y) :- NX is X+1, dentro(NX,Y).
viz(X,Y,NX,Y) :- NX is X-1, dentro(NX,Y).
viz(X,Y,X,NY) :- NY is Y+1, dentro(X,NY).
viz(X,Y,X,NY) :- NY is Y-1, dentro(X,NY).

celula(X,Y) :- map_size(MX,MY), between(1,MX,X), between(1,MY,Y).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Sensores (unico ponto que le o ambiente)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% percepcoes na casa atual: brilho (ouro) e reflexo (item de energia)
sensor_local(L) :- posicao(X,Y,_), tile(X,Y,Z), findall(O, observacao_loc(O,[Z]), L), !.
sensor_local([]).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Base de conhecimento: registro de percepcoes
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% chamada a cada atualiza_obs (inclusive apos teletransporte)
registra_percepcao :-
    posicao(X,Y,D), D \== morto,
    (   percepcao_vista(X,Y,_) -> true
    ;   observacoes(L), assertz(percepcao_vista(X,Y,L))
    ),
    (   sensor_local(Loc), memberchk(reflexo,Loc), \+ u_visto(X,Y)
    ->  assertz(u_visto(X,Y))
    ;   true
    ),
    !.
registra_percepcao.

% Se o ultimo "andar" nao levou o agente ao destino, a casa de destino e
% um teletransportador: nao e casa visitada normal e deve ser evitada.
verifica_teleporte :-
    (   retract(intencao(DX,DY)),
        posicao(X,Y,_),
        ( X \== DX ; Y \== DY )
    ->  assertz(tele(DX,DY)),
        retractall(percepcao_vista(DX,DY,_))
    ;   true
    ).

% Se a energia caiu desde a ultima decisao, a casa atual tem inimigo.
verifica_dano :-
    energia(E), posicao(X,Y,_),
    (   energia_ant(EA), E < EA, \+ bloqueada(X,Y)
    ->  assertz(bloqueada(X,Y))
    ;   true
    ),
    retractall(energia_ant(_)),
    assertz(energia_ant(E)).

atualiza_conhecimento :- verifica_teleporte, verifica_dano.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Inferencia
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Um perigo do tipo S esta descartado em (X,Y) se alguma casa visitada
% vizinha NAO teve a percepcao S (se houvesse o perigo, ela teria sentido).
livre(S,X,Y) :- viz(X,Y,VX,VY), percepcao_vista(VX,VY,L), \+ memberchk(S,L), !.

% Casa segura: visitada (e sem dano/teleporte) ou com poco, inimigo e
% teletransportador todos descartados.
seguro(X,Y) :-
    dentro(X,Y), \+ bloqueada(X,Y), \+ tele(X,Y),
    (   percepcao_vista(X,Y,_) -> true
    ;   livre(brisa,X,Y), livre(passos,X,Y), livre(palmas,X,Y)
    ).

% Casa nao visitada que encosta numa casa visitada
fronteira(X,Y) :-
    dentro(X,Y), \+ percepcao_vista(X,Y,_), \+ bloqueada(X,Y), \+ tele(X,Y),
    viz(X,Y,VX,VY), percepcao_vista(VX,VY,_), !.

%% --- Inferencia de perigos certos e estimativa de risco ---

fonte(S,X,Y) :- percepcao_vista(X,Y,L), memberchk(S,L).

% perigos descobertos na pratica
conhecido(passos,X,Y) :- bloqueada(X,Y).
conhecido(palmas,X,Y) :- tele(X,Y).

% casa nao visitada onde o perigo S ainda nao foi descartado
possivel(S,X,Y) :- dentro(X,Y), \+ percepcao_vista(X,Y,_), \+ livre(S,X,Y).

% a fonte (VX,VY) da percepcao S ja tem um perigo conhecido ao lado
explicada_por_conhecido(S,VX,VY) :- viz(VX,VY,ZX,ZY), conhecido(S,ZX,ZY), !.

% Perigo S certo em (X,Y): alguma casa que sentiu S so tem (X,Y) como
% candidata (as outras vizinhas foram descartadas ou ja foram visitadas).
certo(S,X,Y) :- conhecido(S,X,Y), !.
certo(S,X,Y) :-
    possivel(S,X,Y),
    viz(X,Y,VX,VY), fonte(S,VX,VY),
    \+ explicada_por_conhecido(S,VX,VY),
    findall(Z, ( viz(VX,VY,ZX,ZY), possivel(S,ZX,ZY), Z=(ZX,ZY) ), [(X,Y)]),
    !.

% perigo ja "explicado" por um perigo certo vizinho da fonte
explicada(S,VX,VY) :- viz(VX,VY,ZX,ZY), certo(S,ZX,ZY), !.

% probabilidade (heuristica) de que a fonte V tenha o perigo na casa candidata
prob_fonte(S,VX,VY,P) :-
    (   explicada(S,VX,VY) -> prior(S,P)
    ;   findall(x, ( viz(VX,VY,ZX,ZY), possivel(S,ZX,ZY) ), L),
        length(L,N),
        (   N > 0 -> P is 1.0/N ; prior(S,P) )
    ).

% prob(S,X,Y,P): P=0 se descartado; 1 se certo; senao a maior probabilidade
% entre as fontes adjacentes (a fonte mais "exigente" domina).
prob(S,X,Y,0.0) :- livre(S,X,Y), !.
prob(S,X,Y,1.0) :- certo(S,X,Y), !.
prob(S,X,Y,P) :-
    findall(Pv, ( viz(X,Y,VX,VY), fonte(S,VX,VY), prob_fonte(S,VX,VY,Pv) ), Ps),
    (   Ps == [] -> prior(S,P) ; max_list(Ps,P) ).

% Peso do perigo na situacao atual: o inimigo pesa mais quanto menor a
% energia do agente (dano de ate 80 pode matar).
peso_atual(passos, Pe) :- !,
    energia(E),
    (   E > 80 -> Pe = 150
    ;   E > 50 -> Pe = 400
    ;   Pe = 1000
    ).
peso_atual(S, Pe) :- peso_risco(S, Pe).

% Risco = soma de peso*probabilidade dos tres tipos de perigo
risco(X,Y,R) :-
    findall(V, ( member(S,[brisa,passos,palmas]), peso_atual(S,Pe),
                 prob(S,X,Y,P), V is Pe*P ), Vs),
    sum_list(Vs,R).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Interface com o planejador em Python
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% lista de casas [X,Y] inferidas seguras (o mapa "conhecido" do planejador)
seguras(L) :- findall([X,Y], ( celula(X,Y), seguro(X,Y) ), L).

% o Python avisa para onde vai andar, para detectar teleporte depois
registra_intencao(X,Y) :- retractall(intencao(_,_)), assertz(intencao(X,Y)).

todo_ouro :- ouro_coletado(N), total_ouro(T), N >= T.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Politica: o que o agente quer fazer
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% alvo(Prioridade, Tipo, Dados)
%%   Tipo = acao : Dados e a acao a executar agora (pegar / parar)
%%   Tipo = ir   : Dados e a lista de casas [X,Y] que servem de objetivo;
%%                 o Python escolhe o objetivo mais proximo e planeja a rota.
%%   Tipo = ir_risco : Dados e uma lista de grupos [Risco, Casas], do menor
%%                 para o maior risco.
%% O Python tenta as prioridades de 1 a 8, na ordem, e usa a primeira que
%% der resultado (e, no caso de "ir", a primeira para a qual existe rota).

% 1. morto: nada a fazer
alvo(1, acao, parar) :- posicao(_,_,morto).

% 2. ouro na casa atual
alvo(2, acao, pegar) :-
    sensor_local(L), memberchk(brilho,L),
    retract(ouro_coletado(N)), N1 is N+1, assertz(ouro_coletado(N1)).

% 3. item de energia na casa atual e energia baixa o bastante para aproveitar
alvo(3, acao, pegar) :-
    \+ todo_ouro,
    energia(E), E =< 50,
    sensor_local(L), memberchk(reflexo,L),
    posicao(X,Y,_), retractall(u_visto(X,Y)).

% 4. energia baixa e item de energia conhecido: ir ate ele
alvo(4, ir, Alvos) :-
    \+ todo_ouro,
    energia(E), E =< 50,
    findall([X,Y], u_visto(X,Y), Alvos), Alvos \== [].

% 5. explorar: casas seguras ainda nao visitadas
alvo(5, ir, Alvos) :-
    \+ todo_ouro,
    findall([X,Y], ( celula(X,Y), seguro(X,Y), \+ percepcao_vista(X,Y,_) ), Alvos),
    Alvos \== [].

% 6. sem casas seguras: arriscar casas de fronteira (aceitas ate limite_risco/1).
%    Dados = grupos [Risco, Casas] em ordem crescente de risco; o Python usa
%    o primeiro grupo para o qual existe rota.
alvo(6, ir_risco, Grupos) :-
    \+ todo_ouro,
    limite_risco(Lim),
    findall(R-[X,Y], ( celula(X,Y), fronteira(X,Y), risco(X,Y,R), R =< Lim ), Cs),
    Cs \== [],
    keysort(Cs, Ord),
    group_pairs_by_key(Ord, Pares),
    findall([R,Casas], member(R-Casas, Pares), Grupos).

% 7. todo o ouro coletado ou nada mais a explorar: voltar para [1,1]
alvo(7, ir, [[1,1]]) :- \+ posicao(1,1,_).

% 8. fim: ficar parado (acao sem custo)
alvo(8, acao, parar).

% fim da execucao: ouro todo coletado (ou nada mais a explorar) e agente em [1,1]
parar :- true.