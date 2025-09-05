import socket

class Board:
    def __init__(self, n):
        self.n = n
        self.grid = [[" " for _ in range(n)] for _ in range(n)]

    def display(self):
        print("\n" + "=" * 20)
        for r in range(self.n):
            print(" | ".join(self.grid[r]))
            if r < self.n - 1:
                print("-" * (self.n * 4 - 3))
        print("=" * 20)

    def place(self, row, col, symbol):
        if 0 <= row < self.n and 0 <= col < self.n and self.grid[row][col] == " ":
            self.grid[row][col] = symbol
            return True
        return False
    
    def check_win(self, symbol):
        n = self.n
        g = self.grid
        target = [symbol] * n

        for i in range(n):
            if g[i] == target:
                return True
            if [g[r][i] for r in range(n)] == target:
                return True

        if [g[i][i] for i in range(n)] == target:
            return True
        if [g[i][n - 1 - i] for i in range(n)] == target:
            return True
        return False

    def full(self):
        for r in range(self.n):
            for c in range(self.n):
                if self.grid[r][c] == " ":
                    return False
        return True
    
class Player:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def move(self, board: Board):
        while True:
            try:
                row, col = map(int, input(f"{self.name} ({self.symbol}) enter row col (1-{board.n}): ").split())
                row -= 1
                col -= 1
                if board.place(row, col, self.symbol):
                    break
                else:
                    print("Invalid move")
            except ValueError:
                print("Enter two numbers")  

class Game:
    def __init__(self, n=3):
        self.board = Board(n)
        self.players = [Player("Player 1", "X"), Player("Player 2", "O")]

    def play(self):
        turn = 0
        while True:
            self.board.display()
            current = self.players[turn % 2]
            current.move(self.board)

            if self.board.check_win(current.symbol):
                self.board.display()
                print(f"{current.name} wins")
                break
            if self.board.full():
                self.board.display()
                print("It's a draw")
                break
            turn += 1

class NetworkClient:
    def __init__(self):
        self.socket = None
        self.board = None
        self.player_info = None
        self.game_active = True
        
    def connect_to_server(self, host="0.0.0.0", port=9999):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            print(f"Connected to server at {host}:{port}")
            return True
        except Exception:
            print("Failed to connect")
            return False
            
    def wait_for_message(self):
        try:
            data = self.socket.recv(1024).decode().strip()
            if data:
                parts = data.split("|")
                if len(parts) >= 1:
                    return self.handle_message(parts)
            return True
        except Exception:
            print("Error receiving message")
            return False
                
    def handle_message(self, parts):
        msg_type = parts[0]
        
        if msg_type == 'PLAYER_INFO':
            self.player_info = {
                'player_num': int(parts[1]),
                'symbol': parts[2],
                'name': parts[3]
            }
            print(f"You are {parts[3]} ({parts[2]})")
            return True
            
        elif msg_type == 'BOARD':
            n = int(parts[1])
            if not self.board:
                self.board = Board(n)
            
            grid = []
            for i in range(2, 2 + n):
                row = parts[i].split(",")
                grid.append(row)
            self.board.grid = grid
            self.board.display()
            return True
            
        elif msg_type == 'YOUR_TURN':
            print(f"\n{parts[2]}'s turn")
            self.make_move()
            return True
            
        elif msg_type == 'WAIT_TURN':
            print(f"\nWaiting for {parts[1]} to make a move")
            return True
            
        elif msg_type == 'INVALID_MOVE':
            print(f"\n{parts[1]}")
            self.make_move()
            return True
            
        elif msg_type == 'GAME_OVER':
            if parts[1] == 'WIN':
                winner = parts[2]
                if winner == self.player_info['name']:
                    print(f"\nCongratulations, You won")
                else:
                    print(f"\n{winner} wins")
            else:  # DRAW
                print(f"\nDraw Game")
            self.game_active = False
            return False
        
        return True
            
    def make_move(self):
        while True:
            try:
                move_input = input(f"Enter row col (1-{self.board.n}): ").strip()
                row, col = map(int, move_input.split())
                row -= 1  
                col -= 1
                
                if 0 <= row < self.board.n and 0 <= col < self.board.n:
                    move_data = f"MOVE|{row}|{col}\n"
                    self.socket.send(move_data.encode())
                    break
                else:
                    print(f"Please enter numbers between 1 and {self.board.n}")
                    
            except ValueError:
                print("Please enter two numbers separated by a space")
            except Exception:
                print("Error sending move")
                break
                
    def play(self):
        print("Waiting for game to start")
        
        try:
            while self.game_active:
                if not self.wait_for_message():
                    break
        except KeyboardInterrupt:
            print("\nGame interrupted by user")

        self.socket.close()
        print("Disconnected from server")

def main():
    if NetworkClient().connect_to_server():# pls specify host and port while calling(default is 0.0.0.0)
        NetworkClient().play()
    else:
        print("Could not connect to server")

main()