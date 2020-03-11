
'''A simple blackjack game using python and tkinter'''


import tkinter as tk
import os
from tkinter import simpledialog
import pickle
import random
import sys

class GUICard:
    '''class for the position and the value of cards'''
    theCards = {}

    def __init__(self, card, canvas):
        self.canvas = canvas
        self.value = card.value
        self.symbol = card.symbol
        self.position = None
        self.image = None
        GUICard.theCards[card] = self

    def _fetch_image(self):
        if self.face:
            return CardImages.images[self.symbol][Deck.values.index(self.value)]
        else: return CardImages.images['b']

    def _animate_image(self):
        self.canvas.move(self.image, self.img_vx, self.img_vy)
        x1,y1,x2,y2 = self.canvas.bbox(self.image)
        if abs(x1 - self.position[0]) < 5 and abs(y1 - self.position[1]) < 5:
            return
        else:
            self.canvas.update_idletasks()
            self.canvas.after(20, self._animate_image)

    def set_face(self, face):
        if self.position and face != self.face:
            self.face = face
            self.canvas.itemconfig(self.image, image= self._fetch_image())
        else:
            self.face = face

    def move_to(self, new_position):
        if not self.position: self.position = new_position
        if not self.image:
            self.image = self.canvas.create_image(*self.position, image =  self._fetch_image())
        self.canvas.itemconfig(self.image, anchor='nw')
        if new_position != self.position:
            self.img_vx = (new_position[0] - self.position[0]) / 20
            self.img_vy = (new_position[1] - self.position[1]) / 20
            self._animate_image()
            self.position = new_position

    def __str__(self):
        out = self.value + self.symbol
        if self.position:
            out += '['+str(self.position[0])+','+str(self.position[1])+']'
        return out


class Card:
    # card deck
    gr_names = {'c': 'Clubs ♣', 's': 'Spades ♠', 'h': 'Hearts ♥', 'd': 'Diamonds ♦',
                'A': 'Ace', '2': 'Two', '3': 'Three', '4':'Four', '5':'Five', '6':'Six', '7':'Seven', '8':'Eight',
                '9': 'Nine', 'T': 'Ten', 'J': 'Jack', 'Q':'Queen', 'K': 'King'}
    the_cards = []

    def __init__(self, value, symbol):
        self.value = value.upper().strip()
        self.symbol = symbol.lower().strip()
        Card.the_cards.append(self)

    def __str__(self):
        return self.value+self.symbol


class Deck:
    '''class which creates the cards for blackjack'''
    symbols = "shcd" #  cards categories for spades, hearts, clubs and diamonds
    values =  "A23456789TJQK" # cards values

    def __init__(self):
        self.content = []  # cards on deck
        self.pile = []  # cards players have
        for s in Deck.symbols:
            for v in Deck.values:
                self.content.append(Card(v,s))

    def shuffle(self):
        random.shuffle(self.content)

    def draw(self):
        if len(self.content)< 1 : return 'empty deck'
        drawn_card = self.content.pop(0)
        self.pile.append(drawn_card)
        return drawn_card


class CardImages:
    '''class which creates the cards from the spritesheet'''
    """ Get absolute path to resource, works for dev and for PyInstaller """
    image_file = 'cards2.gif'
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        path = sys._MEIPASS
    except Exception:
        path = os.path.abspath(".")
    imagefile = os.path.join(path, image_file)

    images = {}
    @staticmethod
    def generate_card_images():
        # create small pictures of cards (79 X 123) from the spritesheet cards2.gif
        num_sprites = 13
        place = 0
        spritesheet = tk.PhotoImage(file= CardImages.imagefile)
        for x in 'sdhc':
            CardImages.images[x] = [CardImages._subimage(79 * i, 0 + place, \
                                                         79 * (i + 1), 123 + place, spritesheet) for i in range(num_sprites)]
            place += 123
        CardImages.images['b'] = CardImages._subimage(0, place, 79, 123 + place, spritesheet) #back image
    @staticmethod
    def _subimage(l, t, r, b, spritesheet):
        dst = tk.PhotoImage()
        dst.tk.call(dst, 'copy', spritesheet, '-from', l, t, r, b, '-to', 0, 0)
        return dst

class Player():
    ''' class which creates the players behavior '''
    def __init__(self, name, deck):
        self.name = name
        self.deck = deck
        self.score = 0

    def _check_if_exceeded(self):
        if self.score > 21:
            self.score = -1

    def _calculate_value(self, card):
        if card.value.isdigit(): return int(card.value)
        elif card.value == 'A':
            return 1 #
        else: return 10 # refers to values of T,J,Q,K


class ComputerPlayer(Player):
    '''class which controls the computer player behavior'''
    def __init__(self, canvas, deck):

        self.canvas = canvas
        self.name = 'CPU'
        self.deck = deck
        self.score = 0
        self.hand = []  # player's cards
        self.start = GUI.padx, GUI.pady  # position of players cards
        self.next_card_position = self.place_of_next_card()
        self.message_place = self.start[0], round(self.start[1] + GUI.card_height * 1.1)
        self.infomessage = ''
        self.my_message = self.canvas.create_text(*self.message_place, fill='white', text=self.infomessage, font='Arial 30', anchor='nw')


        self.active = False

    def place_of_next_card(self):
        return self.start[0] + (GUI.card_width // 2) * len(self.hand), self.start[1]

    def receive(self, card):  # adds a new card to player
        self.hand.append(card)
        self.next_card_position = self.place_of_next_card()
        return len(self.hand) - 1

    def plays(self, face=False):
        if self.active:
            card = GUICard.theCards[self.deck.draw()]
            card.set_face(face)
            card.move_to(self.place_of_next_card())
            self.receive(card)
            card_value = self._calculate_value(card)
            self.score += card_value
            self._check_if_exceeded()
            if self._computer_strategy():
                root.after(1000, self.plays)
            else:
                self.show_cards()
                self.active = False
                if self.score == -1:
                    self.update_message()


    def show_cards(self, all=False):
        if self.score == -1 or all:
            for card in self.hand:
                card.set_face(True)
        else:
            card_to_hide = random.randint(0, len(self.hand)-1)
            for i, card in enumerate(self.hand):
                if i != card_to_hide:
                    card.set_face(True)

    def _computer_strategy(self):
        return False if self.score >= 16 or self.score == -1 else True  #

    def update_message(self):
        if self.score == -1:
            self.infomessage = self.name + ': You lose..'
            self.canvas.itemconfig(self.my_message, text=self.infomessage)

        else:
            self.infomessage = self.name + ': Your score is ' + str(self.score)
            self.canvas.delete(self.my_message)
            self.canvas.itemconfig(self.my_message, text=self.infomessage)

        self.my_message = self.canvas.create_text(*self.message_place, fill='white', text=self.infomessage,
                                                  font='Arial 30', anchor='nw')


class HumanPlayer(ComputerPlayer):
    '''class concerning the human player'''
    def __init__(self, *args, **kwds, ):
        ComputerPlayer.__init__(self, *args, **kwds)
        self.start = GUI.padx, GUI.board_height - GUI.pady - GUI.card_height  # deck_with_cards_area
        self.message_place = self.start[0], round(self.start[1] - 0.6 * GUI.card_height)
        # checks if this is the first game and asks the player to give a name
        # if the player doesn't give a name he takes the name 'Player' by default
        # if he takes a name by default, he has the opportunity to change it in a new game
        # in order to save his score later
        if app.count_games == 0 or app.username == 'Player':
            self.name = simpledialog.askstring(title='Player name:', prompt='Give a name')
        else:
            self.name = app.username
        if not self.name:
            self.name = 'Player'

    def plays(self, face=True):
        if self.active:
            card = GUICard.theCards[self.deck.draw()]
            card.set_face(face)
            card.move_to(self.place_of_next_card())
            self.receive(card)
            card_value = self._calculate_value(card)
            self.score += card_value
            self._check_if_exceeded()
            self.update_message()
            root.update_idletasks()
            if self.score == -1:
                self.active = False
                app.find_winner()


class GUI():
    '''class for the graphic environment of the program'''
    board_width, board_height = 1100, 700  # canvas dimensions
    card_width, card_height = 79, 123  # card dimensions
    padx, pady = 50, 50
    deck = (800, 230)
    # deck area
    deck_of_cards_area = (deck[0], deck[1], deck[0] + card_width, deck[1] + card_height)

    @staticmethod
    def in_area(point, rect):
        if point[0] >= rect[0] and point[0] <= rect[2] and point[1] >= rect[1] and point[1] <= rect[3]:
            return True
        else:
            return False


class GUIGame(GUI):
    'Basic class for the graphics of the game, creates the surface, the widgets and the players of the game'

    def __init__(self, root):
        ##### Game parameters
        self.root = root
        root.title("BlackJack")
        root.resizable(width='false', height='false')
        ##### GUI parameters
        self.infomessage_position = GUI.padx, GUI.board_height // 2 - 22
        self.top_font = 'Arial 16'
        self.f = tk.Frame(root)
        self.f.pack(expand=True, fill='both')
        self.create_widgets()
        self.deck = Deck()
        self.run = False
        self.winner = None
        self.username = None

    def create_widgets(self):
        self.f1 = tk.Frame(self.f)
        self.f1.pack(side='top', expand=True, fill='x', padx=0, pady=1)
        self.button_rules = tk.Button(self.f1, text='Rules', font=self.top_font, bg='darkred', fg='white',
                                      command=self.show_rules)
        self.button_rules.pack(side='left')
        self.button_start = tk.Button(self.f1, text='New game', font=self.top_font, bg='darkred', fg='white',
                                      command=self.play_game)
        self.button_start.pack(side='left')
        self.button_save = tk.Button(self.f1, text='Save score', font=self.top_font, bg='darkred', fg='white',
                                     command=self.save_score)
        self.button_save.pack(side='left')
        self.button_save.configure(state='disabled')
        self.button_highScores = tk.Button(self.f1, text='High Scores', font=self.top_font, bg='darkred', fg='white',
                                           command=self.info)
        self.button_highScores.pack(side='left')

        self.f2 = tk.Frame(self.f)
        self.f2.pack(fill='both')
        self.canvas = tk.Canvas(self.f2, width=self.board_width, \
                                height=self.board_height, bg='darkgreen')
        self.canvas.pack(side='left', fill='x', expand=1)
        self.button_stop = tk.Button(self.f1, text='Check Winner', font=self.top_font, bg='darkred', fg='white',
                                     command=self.stop)
        self.button_stop.pack(side='left')
        self.button_stop.configure(state='disabled')
        self.canvas.bind("<Button-1>", self.board_event_handler)
        self.message = ""
        self.canvas_info_message = ''
        self.username = 'Player'
        self.score = [0, 0]
        self.thescore = tk.StringVar()
        self.thescore.set('Score is CPU: ' + str(self.score[0]) + ' VS ' + self.username + ': ' + str(self.score[1]))
        self.score_label = tk.Label(self.f1, textvariable=self.thescore, font='Arial 20', bg='darkred', fg='white').pack(
            side='right')
        # count your games
        self.count_games = 0

    def save_score(self):
        # save the score of the game using pickle
        score_file = 'pickle0.dat'
        high_scores = []
        # first time your run this dat file won't exist
        if self.username != 'Player' and os.path.exists(score_file):
            with open(score_file, 'rb') as f:
                high_scores = pickle.load(f)

        # add elements of the list
        self.scores = self.score[0] + self.score[1]
        # calculate the percentage of wins
        self.percent = self.score[1] / self.scores * 100

        scores = [self.username, self.score[0], self.score[1], self.percent, self.count_games]

        high_scores.append(scores)
        # fill database
        with open(score_file, 'wb') as f:
            pickle.dump(high_scores, f)
        # reload database
        with open(score_file, 'rb') as f:
            high_scores = pickle.load(f)
        self.button_save.configure(state='disabled')
        print(high_scores)

    def info(self):
        scores = []
        if os.path.isfile('pickle0.dat'):
            with open('pickle0.dat', 'rb') as f:
                scores = pickle.load(f)
                # first sorted based on the percentage of the winning games(self.percent)
                # and if some are equal sorted based on number of games(self.count_games)
                scores = sorted(scores, key=lambda x: (x[3], x[4]), reverse=True)
            give_scores = ''
            for n, f in enumerate(scores):
                give_scores += ('CPU - ' + '{:16}: '.format(f[0][0:25]) + str(f[1]) + ' - ' + str(
                    f[2]) + '\t' + '(' + '{0:.0f}'.format(f[3]) + '%)' + '\n' + '\n')
                if n == 9: break

        message = 'Top 10 scores of the game!\n \n' + str(give_scores)
        w = tk.Toplevel()
        w.geometry('+{}+{}'.format(self.root.winfo_x() + 120, self.root.winfo_y() + 120))
        w.title('Highest Scores in BlackJack')
        l = tk.Label(w, text=message, font="Courier", anchor="nw", justify="left", bg='darkred', fg='white').pack(
            expand=True, fill="both")
        toplevel_ok = tk.Button(w, text='Close', font='Courier', bg='gray', command=w.destroy).pack(expand=True,
                                                                                                 fill='both')
        # click Close button to close the window

    def show_rules(self):
        message = 'The player attempts to beat the CPU, which is the dealer by getting\n' \
                  'a count as close to 21 as possible, without going over 21.\n' \
                  '(Press the Check Winner Button in order to stop drawing)\n \n' \
                  'If the game is tied the dealer wins.\n' \
                  'Face cards count for 10 and any other card is its pip value.\n \n' \
                  'You can save your score only if you have given \n' \
                  'a name and you have played more than two games. \n \n' \
                  'You can also view your High Scores!\n \n' \
                  'Good Luck!'
        w = tk.Toplevel()
        w.geometry('+{}+{}'.format(self.root.winfo_x() + 120, self.root.winfo_y() + 120))
        w.title('Rules of the game')
        l = tk.Label(w, text=message, font="Courier", anchor="nw", justify="left", bg='darkred', fg='white').pack\
            (expand= True, fill="both")
        toplevel_ok = tk.Button(w, text='Close', font='Courier', bg='gray', command=w.destroy).pack(expand=True,
                                                                                                 fill='both')

    def play_game(self):
        self.deck = Deck()
        self.deck.shuffle()
        self.computer = ComputerPlayer(self.canvas, self.deck)
        self.human = HumanPlayer(self.canvas, self.deck)
        self.username = self.human.name
        self.thescore.set('Score is CPU: ' + str(self.score[0]) + ' VS ' + self.username + ': ' + str(self.score[1]))
        self.canvas.delete('all')
        for card in self.deck.content:
            c = GUICard(card, self.canvas)
            c.set_face(False)
            c.move_to(GUI.deck)
        self.run = True
        # disable start button, enable stop button
        self.button_start.configure(state='disabled')
        self.button_stop.configure(state='normal')
        self.winner = None
        self.computer.active = True
        self.computer.plays()
        # human to play
        root.update_idletasks()
        if self.computer.score == -1:
            root.after_idle(self.stop_drawing_cards)
            self.stop()
        else:
            root.after_idle(self.human_turn)
        # counts the games
        self.count_games += 1

    def human_turn(self):
        self.human.active = True

    def board_event_handler(self, event):
        x = event.x
        y = event.y
        if self.human.active and self.human.score != -1:
            if self.computer.active is False:
                self.human.plays()

    def find_winner(self):  # decides the winner
        max_score = max(self.computer.score, self.human.score)
        if max_score == -1:
            the_winner_is = 'No winner!'
            winner = False
        else:
            winner = 'human' if self.human.score == max_score else 'computer'
            if self.computer.score == self.human.score:
                winner = 'computer'
            the_winner_is = self.human.name if winner == 'human' else self.computer.name
            article = 'is'
            the_winner_is = 'Winner {} {} !!!'.format(article, the_winner_is)

        self.computer.show_cards(all=True)
        self.computer.update_message()
        self.pop_up(the_winner_is)
        self.run = False
        self.winner = None
        self.human.active = False
        # enable start button, disable stop button
        self.button_start.configure(state='normal')
        self.button_stop.configure(state='disabled')
        # check score
        if self.computer.score > self.human.score:
            app.score[0] += 1
        elif self.computer.score < self.human.score:
            app.score[1] += 1
        elif self.computer.score == self.human.score and not self.computer.score == -1:
            app.score[0] += 1
        elif self.computer.score == -1 and self.human.score == -1:
            app.score
        self.thescore.set('Score: CPU  ' + str(self.score[0]) + ' vs ' + self.username + ': ' + str(self.score[1]))
        # enables the save score button:
        if self.score[0] + self.score[1] >= 3 and app.username != 'Player':
            self.button_save.configure(state='normal')

    def pop_up(self, msg):
        tk.messagebox.showinfo('Result', msg)

    def stop(self):
        self.stop_drawing_cards()

    def stop_drawing_cards(self):
        self.find_winner()
        self.canvas.update_idletasks()


if __name__ == '__main__':
    root = tk.Tk()
    CardImages.generate_card_images()
    app = GUIGame(root)
    root.mainloop()

