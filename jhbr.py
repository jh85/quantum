#!/usr/bin/env python3

import copy
import random
from cshogi import Board, move_to_usi
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from qiskit import QuantumCircuit, transpile, execute
from qiskit_aer import AerSimulator


CHECKMATE_SCORE = 30000
DEPTH_LIMIT = 3
DEBUG = True

def mark_good(qc, target=0):
    n = qc.num_qubits - 1
    target_bin = bin(target)[2:].zfill(n)
    zero_locations = [i for i,x in enumerate(target_bin) if '0' == x]
    qc.x(zero_locations)
    qc.mcx([i for i in range(n)], n)
    qc.x(zero_locations)
    return qc

def sort_counts(counts):
    return [k for k,v in sorted(counts.items(),
                                key=lambda itm:itm[1], reverse=True)]

def grover_search2(allmoves, good, bad):
    return good[0]

def grover_search(allmoves, good, bad):
    t1 = time.time()
    n = 10 # len(bin(len(allmoves)-1)[2:])
    mv2idx = {v:k for k,v in list(enumerate(allmoves))}
    idx2mv = {k:v for k,v in list(enumerate(allmoves))}
    good_idx = mv2idx[good[0]]
    qc = QuantumCircuit(n + 1, n)
    qc.x(n)
    qc.h(range(n + 1))
    k = len(good)
    r = int(np.pi * np.sqrt(2**n/k) / 4)  # Number of iterations
    for _ in range(r):
        qc = mark_good(qc, target=good_idx)
        # Diffusion operation
        qc.h(range(n))
        qc.x(range(n))
        qc.h(n - 1)
        qc.mcx([i for i in range(n-1)], n - 1)
        qc.h(n - 1)
        qc.x(range(n))
        qc.h(range(n))
    qc.measure(range(n), range(n))
    backend = AerSimulator()
    compiled_circuit = transpile(qc, backend)
    job = backend.run(compiled_circuit, shots=1000)
    best_state = sort_counts(job.result().get_counts())[0]
    bestmove = idx2mv[int(best_state[::-1],2)]

    t2 = time.time()
    if DEBUG == True:
        with open("jhbr.log", "a") as f:
            f.write(f"allmoves = {len(allmoves)} good = {str(good)} bestmove = {bestmove} time = {t2-t1}\n")

    return bestmove

def change_of_turn(turn):
    if turn == "sente":
        return "gote"
    else:
        return "sente"

evaluate_count = 0    
def evaluate(board):
    global evaluate_count
    evaluate_count += 1
    
    bishop_value = 10
    rook_value = 12
    to_score = lambda x: x[0]*1 + x[1]*2 + x[2]*3 + x[3]*4 + x[4]*7 + x[5]*bishop_value +  x[5]*rook_value

    b = board.pieces
    sente_hand,gote_hand = board.pieces_in_hand

    # gote
    gote_pieces = list(filter(lambda x: x & 0b10000, b))
    gote_bishops = len(list(filter(lambda x: (x&0b111 ==  0b101) and (x > 16), b))) * (bishop_value-5)
    gote_rooks = len(list(filter(lambda x: (x&0b111 ==  0b110) and (x > 16), b))) * (rook_value-6)
    gote = sum(gote_pieces) - 16*len(gote_pieces) + to_score(gote_hand) + gote_bishops + gote_rooks

    # sente
    sente_pieces = list(filter(lambda x: x & 0b10000 == 0, b))
    sente_bishops = len(list(filter(lambda x: (x&0b111 ==  0b110) and (x < 16), b))) * (bishop_value-5)
    sente_rooks = len(list(filter(lambda x: (x&0b111 ==  0b101) and (x < 16), b))) * (rook_value-6)
    sente = sum(sente_pieces) + to_score(sente_hand) + sente_bishops + sente_rooks

    return sente - gote

def negamax_level(board, depth, yomisuji_lst, turn):
    if turn == "sente":
        negamax_score_lst = [yomisuji_lst, -CHECKMATE_SCORE-1]
    else:
        negamax_score_lst = [yomisuji_lst, CHECKMATE_SCORE+1]
    move_lst = list(board.legal_moves)
    
    if len(move_lst) == 0:
        if turn == "sente":
            score = -CHECKMATE_SCORE
        else:
            score = CHECKMATE_SCORE
        return [yomisuji_lst, score]

    if depth == DEPTH_LIMIT:
        score = evaluate(board)
        return [yomisuji_lst, score]
    else:
        random.shuffle(move_lst)
        for mv in move_lst:
            board.push(mv)
            yomisuji_next_lst = yomisuji_lst + [mv]
            turn = change_of_turn(turn)
            score_lst = negamax_level(board, depth+1, yomisuji_next_lst, turn)
            turn = change_of_turn(turn)
            board.pop()

            if turn == "sente":
                tmp_score = score_lst[1]
                max_score = negamax_score_lst[1]
            else:
                tmp_score = -score_lst[1]
                max_score = -negamax_score_lst[1]
                
            if tmp_score > max_score:
                negamax_score_lst = copy.deepcopy(score_lst)
        return negamax_score_lst

class JHBR:
    name = "JHBR"

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.root_board = Board()
        self.player = "sente" # player to play

    def usi(self):
        print("id name " + self.name)

    def usinewgame(self):
        pass
        
    def setoption(self, args):
        pass

    def isready(self):
        self.root_board.reset()

    def position(self, sfen, usi_moves):
        if sfen == "startpos":
            self.root_board.reset()
        elif sfen[:5] == "sfen ":
            self.root_board.set_sfen(sfen[5:])
        for usi_move in usi_moves:
            move = self.root_board.push_usi(usi_move)

    def set_limits(self, btime=None, wtime=None, byoyomi=None,
                   binc=None, winc=None, nodes=None, infinite=False, ponder=False):
        if infinite or ponder:
            self.halt = 2**31-1
        else:
            self.halt = nodes

    def run(self):
        while True:
            cmd_line = input().strip()
            cmd = cmd_line.split(' ', 1)
            
            if cmd[0] == 'usi':
                self.usi()
                print('usiok', flush=True)
            elif cmd[0] == 'setoption':
                option = cmd[1].split(' ')
                self.setoption(option)
            elif cmd[0] == 'isready':
                self.isready()
                print('readyok', flush=True)
            elif cmd[0] == 'usinewgame':
                self.usinewgame()
            elif cmd[0] == 'position':

                if DEBUG == True:
                    with open("jhbr2.log", "a") as f:
                        f.write(str(cmd) + "\n")
                
                args = cmd[1].split('moves')
                self.position(args[0].strip(), args[1].split() if len(args) > 1 else [])
            elif cmd[0] == 'go':
                kwargs = {}
                if len(cmd) > 1:
                    args = cmd[1].split(' ')
                    if args[0] == 'infinite':
                        kwargs['infinite'] = True
                    else:
                        if args[0] == 'ponder':
                            kwargs['ponder'] = True
                            args = args[1:]
                        for i in range(0, len(args) - 1, 2):
                            if args[i] in ['btime', 'wtime', 'byoyomi', 'binc', 'winc', 'nodes']:
                                kwargs[args[i]] = int(args[i + 1])
                self.set_limits(**kwargs)
                # save info for ponderhit
                last_limits = kwargs
                need_print_bestmove = 'ponder' not in kwargs and 'infinite' not in kwargs

                def go_and_print_bestmove():
                    bestmove, ponder_move = self.go()
                    if need_print_bestmove:
                        print('bestmove ' + bestmove + (' ponder ' + ponder_move if ponder_move else ''),
                              flush=True)
                    return bestmove, ponder_move
                self.future = self.executor.submit(go_and_print_bestmove)
            elif cmd[0] == 'stop':
                need_print_bestmove = False
                self.stop()
                bestmove, _ = self.future.result()
                print('bestmove ' + bestmove, flush=True)
            elif cmd[0] == 'ponderhit':
                last_limits['ponder'] = False
                self.ponderhit(last_limits)
                bestmove, ponder_move = self.future.result()
                print('bestmove ' + bestmove + (' ponder ' + ponder_move if ponder_move else ''), flush=True)
            elif cmd[0] == 'quit':
                self.quit()
                break
            
    def go(self):
        self.begin_time = time.time()
        
        if self.root_board.is_game_over():
            return "resign", None

        if self.root_board.is_nyugyoku():
            return "win", None

        if len(list(self.root_board.legal_moves)) == 0:
            return "resign", None
        else:
            player = "sente" if self.root_board.turn == 0 else "gote"
            move_lst_searched = negamax_level(self.root_board, 0, [], player)
            bestmove = move_lst_searched[0][0]
            bestmove_by_G = grover_search(list(self.root_board.legal_moves), good=[bestmove], bad=[])
            return move_to_usi(bestmove_by_G), None

    def stop(self):
        self.halt = 0

    def ponderhit(self, last_limits):
        pass

    def quit(self):
        self.stop()

def main():
    player = JHBR()
    player.run()

main()
