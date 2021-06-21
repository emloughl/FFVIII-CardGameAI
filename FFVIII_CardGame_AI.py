'''
 ___ _           _   ___         _                 __   _____ ___ ___ 
 | __(_)_ _  __ _| | | __|_ _ _ _| |_ __ _ ____  _  \ \ / /_ _|_ _|_ _|
 | _|| | ' \/ _` | | | _/ _` | ' \  _/ _` (_-< || |  \ V / | | | | | | 
 |_| |_|_||_\__,_|_| |_|\__,_|_||_\__\__,_/__/\_, |   \_/ |___|___|___|
   ___             _    ___                   |__/ ___                 
  / __|__ _ _ _ __| |  / __|__ _ _ __  ___    /_\ |_ _|                
 | (__/ _` | '_/ _` | | (_ / _` | '  \/ -_)  / _ \ | |                 
  \___\__,_|_| \__,_|  \___\__,_|_|_|_\___| /_/ \_\___|                
                                                              
Title: Final Fantasy VIII Card Game AI
Author: Evan Loughlin
Date: June 20, 2021

This program provides recommendations for the "Best Move", given a particular game state.
A simple Minimax algorithm is implemented for this purpose.
The starting game state can be input in gamestate.yaml, specifying each of the 10 cards
in the game, their owner, their position (either "Hand" or 1-9), and the card strength values.

Refer to README.md for detailed instructions.
'''

import yaml
import argparse
import os
from enum import Enum
import copy
import math

# Constants
PLAYER = "P"
OPPONENT = "O"


class Card:
    def __init__(self, symbol, owner, top, left, right, bottom):
        self.symbol = symbol
        self.top = top
        self.left = left
        self.right = right
        self.bottom = bottom
        # Owner: Whether card is flipped for Player (P) or Opponent (O)
        self.owner = owner

    def __str__(self):
        output = "  {}-{}  \n".format(self.symbol, self.owner)
        output += " | {} | \n".format(self.top)
        output += " |{} {}| \n".format(self.left, self.right)
        output += " | {} | \n".format(self.bottom)
        return output
        


def display_cards_horizontally(cards):
    '''
    Given a list of Card objects, returns an string showing the objects horizontally
    '''
    line1 = ""
    line2 = ""
    line3 = ""
    line4 = ""
    for card in cards:
        if card == None:
            line1 += "       "
            line2 += " |   | "
            line3 += " |   | "
            line4 += " |   | "
        else:
            line1 += "  {}-{}  ".format(card.symbol, card.owner)
            line2 += " | {} | ".format(card.top)
            line3 += " |{} {}| ".format(card.left, card.right)
            line4 += " | {} | ".format(card.bottom)

    return "{}\n{}\n{}\n{}\n".format(line1,line2,line3,line4)

class Player:
    def __init__(self, name):
        self.name = name
        # Hand is a dict of [Card Symbol] -> Card Object
        self.hand = {}

    def __str__(self):
        output = "Player {} Hand:".format(self.name)

class GameState:
    def __init__(self):
        # Cell Positions are treated like a NUMPAD 
        #
        #   7  8  9
        #   4  5  6
        #   1  2  3
        self.board = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}

        self.players = {PLAYER: Player(name=PLAYER), OPPONENT: Player(name=OPPONENT)}

        self.current_player = None

        self.points = {PLAYER: 0, OPPONENT: 0}

        self.previous_gamestate = None
    
    def get_winner(self):
        if self.points[PLAYER] > self.points[OPPONENT]:
            return PLAYER
        else:
            return OPPONENT
    
    def game_over(self):
        '''
        Returns whether the game is over.
        '''
        return len(self.get_available_positions()) == 0

    def get_opposite_player(self):
        if self.current_player == PLAYER:
            return OPPONENT
        else: 
            return PLAYER

    def make_move(self, card_symbol, position):

        card = self.players[self.current_player].hand[card_symbol]
        # print("MAKE MOVE")
        # print(card)

        # Remove from hand
        del self.players[self.current_player].hand[card_symbol]

        self.board[position] = card
        self.points[self.current_player] += 1

        other_player = self.get_opposite_player()

        neighbour_cards = self.get_neighbours(position)

        # Update card ownership if power values exceed adjacent card power values
        
        # Neighbour card is above current card
        neighbour_card = neighbour_cards["above"]
        if neighbour_card != None:
            if neighbour_card.owner == other_player:
                if card.top > neighbour_card.bottom:
                    neighbour_card.owner = self.current_player
                    self.points[self.current_player] += 1
                    self.points[other_player] -= 1
        
        # Neighbour card is left of current card
        neighbour_card = neighbour_cards["left_of"]
        if neighbour_card != None:
            if neighbour_card.owner == other_player:
                if card.left > neighbour_card.right:
                    neighbour_card.owner = self.current_player
                    self.points[self.current_player] += 1
                    self.points[other_player] -= 1

        # Neighbour card is right of current card
        neighbour_card = neighbour_cards["right_of"]
        if neighbour_card != None:
            if neighbour_card.owner == other_player:
                if card.right > neighbour_card.left:
                    neighbour_card.owner = self.current_player
                    self.points[self.current_player] += 1
                    self.points[other_player] -= 1

        # Neighbour card is below current card
        neighbour_card = neighbour_cards["below"] 
        if neighbour_card != None:
            if neighbour_card.owner == other_player:
                if card.bottom > neighbour_card.top:
                    neighbour_card.owner = self.current_player
                    self.points[self.current_player] += 1
                    self.points[other_player] -= 1

        # Switch the current player 
        self.current_player = other_player

    def next_possible_moves(self):
        next_moves = []
        available_cards = list(self.players[self.current_player].hand.keys())
        available_positions = self.get_available_positions()

        for position in available_positions:
            for card in available_cards:
                next_moves.append((card, position))

        return next_moves

    def get_available_positions(self):
        '''
        Return a list of integers of available positions that can be played.
        '''
        available_positions = []
        for position in self.board:
            if self.board[position] == None:
                available_positions.append(position)
        return available_positions 

    def get_neighbours(self, position):
        '''
        For a given position (int), provide list of neighbouring cards on the board.
        Positions are laid out like a NUM-PAD

        7 8 9
        4 5 6
        1 2 3
        '''
        neighbours = {"left_of": None, "above": None, "right_of": None, "below": None}

        if position == 7:
            neighbours["below"] = self.board[4]
            neighbours["right_of"] = self.board[8]
        elif position == 8:
            neighbours["left_of"] = self.board[7]
            neighbours["below"] = self.board[5]
            neighbours["right_of"] = self.board[9]
        elif position == 9:
            neighbours["left_of"] = self.board[8]
            neighbours["below"] = self.board[6]
        elif position == 4:
            neighbours["right_of"] = self.board[5]
            neighbours["above"] = self.board[7]
            neighbours["below"] = self.board[1]
        elif position == 5:
            neighbours["right_of"] = self.board[6]
            neighbours["left_of"] = self.board[4]
            neighbours["above"] = self.board[8]
            neighbours["below"] = self.board[2]
        elif position == 6:
            neighbours["left_of"] = self.board[5]
            neighbours["above"] = self.board[9]
            neighbours["below"] = self.board[3]
        elif position == 1:
            neighbours["right_of"] = self.board[2]
            neighbours["above"] = self.board[4]
        elif position == 2:
            neighbours["right_of"] = self.board[3]
            neighbours["left_of"] = self.board[1]
            neighbours["above"] = self.board[5]
        elif position == 3:
            neighbours["above"] = self.board[6]
            neighbours["left_of"] = self.board[2]

        return neighbours

    def __str__(self):
        board_output = "-------------------------------------------\nCurrent Player: {}  |  Points: P = {}, O = {}\n" \
                            .format(self.current_player, self.points[PLAYER], self.points[OPPONENT])
        board_output += display_cards_horizontally([self.board[7], self.board[8], self.board[9]]) + "\n"
        board_output += display_cards_horizontally([self.board[4], self.board[5], self.board[6]]) + "\n"
        board_output += display_cards_horizontally([self.board[1], self.board[2], self.board[3]]) + "\n"
        player_cards_output = display_cards_horizontally(self.players[PLAYER].hand.values())
        opp_cards_output = display_cards_horizontally(self.players[OPPONENT].hand.values())
        return "Player (P) Cards:\n{}\n\nOpponent (O) Cards:\n{}\n\nBoard:\n{}".format(player_cards_output, opp_cards_output, board_output)

# Reference: https://levelup.gitconnected.com/mastering-tic-tac-toe-with-minimax-algorithm-3394d65fa88f
def minimax(gamestate, isMaxTurn, depth, max_depth, player):
    '''
    Uses a Minimax tree to recommend the best next move for the player
    '''
    other_player = gamestate.get_opposite_player()
    if gamestate.game_over() or depth == max_depth:
        return gamestate.points[player] - gamestate.points[other_player]
    
    scores = []
    for move in gamestate.next_possible_moves():
        new_gamestate = copy.deepcopy(gamestate)
        card_symbol, position = move
        new_gamestate.make_move(card_symbol, position)
        scores.append(minimax(new_gamestate, not isMaxTurn, depth + 1, max_depth, player))
    
    return max(scores) if isMaxTurn else min(scores)

def best_move(gamestate, max_depth = 3):
    bestScore = -math.inf
    bestMove = None

    for move in gamestate.next_possible_moves():
        card_symbol, position = move
        new_gamestate = copy.deepcopy(gamestate)
        new_gamestate.make_move(card_symbol, position)

        score = minimax(new_gamestate, True, 1, max_depth, gamestate.current_player)
        if score > bestScore:
            bestScore = score
            bestMove = move
    
    return bestMove, bestScore

def gamestate_from_file(filepath):
    '''
    Generate a GameState object from a file
    '''

    with open(filepath) as f:
        dataMap = yaml.safe_load(f)

    gamestate = GameState()
    gamestate.current_player = dataMap["Current_Player"]

    for card_id in dataMap["Cards"]:
        card_details = dataMap["Cards"][card_id]
        card = Card(symbol=card_details["symbol"],
                    owner=card_details["owner"],
                    top=card_details["top"],
                    left=card_details["left"],
                    right=card_details["right"],
                    bottom=card_details["bottom"])
        position = card_details['position']
        if position == "Hand":
            gamestate.players[card_details["owner"]].hand[card_details["symbol"]] = card
        else:
            gamestate.board[position] = card
    return gamestate

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    return arg

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='filepath', required=True,
                        help="Filepath of GameState file (gamestate.yaml)", type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-d', dest='depth', required=True,
                        help="Max tree depth of Minimax tree", type=int)
    parser.add_argument('-s', dest='starting_player', required=True, type=str, help="Starting Player ('P' for Player, or 'O' for Opponent)")
    return parser.parse_args()

def main():
    args = parse_args()
    gamestate = gamestate_from_file(args.filepath)
    gamestate.starting_player = args.starting_player
    turn_count = 0

    while(not gamestate.game_over()):
        print(gamestate)

        if gamestate.current_player == PLAYER:
            print("Determining best move...")
            bestMove, bestScore = best_move(gamestate, args.depth + turn_count)
            print("* Best Move = ({}, Score = {})".format(bestMove, bestScore))

        print("Player {}: Make a move:".format(gamestate.current_player))

        while (True):
            available_card_symbols = list(gamestate.players[gamestate.current_player].hand.keys())
            card_symbol = input("Choose a card to place (Available = {}.".format(available_card_symbols))
            if card_symbol in available_card_symbols:
                break
            else:
                print("Invalid input... try again.")

        while(True):
            available_positions = gamestate.get_available_positions()
            try:
                position = int(input("Choose a position: (Available = {})".format(available_positions)))
                if position in available_positions:
                    break
                else:
                    print("Invalid input... try again.")
            except:
                print("Invalid input... try again.")

        turn_count += 1
        gamestate.make_move(card_symbol, position)

    print(gamestate)
    print("Winner is {}. Final score: {}".format(gamestate.get_winner(), gamestate.points))

if __name__ == "__main__":
    main()