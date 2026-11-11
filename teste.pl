% Teste headless: imita o ciclo do gmap.py (executa_acao -> acao -> atualiza_obs, verifica_player)
% uso: swipl -q -g "rodar(Seed,Max)" -t halt teste.pl
:- consult('main.pl').

conta_ouro(N) :- findall(x, tile(_,_,'O'), L), length(L,N).

rodar(Seed, Max) :-
    set_random(seed(Seed)),
    reset_game,
    conta_ouro(O0),
    atualiza_obs, verifica_player,
    loop(0, Max, N),
    conta_ouro(O1), Ouro is O0 - O1,
    pontuacao(P), energia(E),
    ( posicao(_,_,morto) -> Vivo = morto ; Vivo = vivo ),
    format("seed=~w acoes=~w pontos=~w energia=~w ouro=~w/~w ~w~n", [Seed,N,P,E,Ouro,O0,Vivo]).

loop(N, Max, N) :- ( posicao(_,_,morto) ; N >= Max ), !.
loop(N, Max, R) :-
    findall(A, executa_acao(A), [A]),          % deve ser deterministica
    (   A == parar -> R = N
    ;   call(A), atualiza_obs, verifica_player,
        N1 is N+1, loop(N1, Max, R)
    ).