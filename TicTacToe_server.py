import socket

class Board:
    def __init__(self, n):
        self.n = n
        self.grid = [[" " for _ in range(n)] for _ in range(n)]

    def display(self):
        for r in range(self.n):
            print(" | ".join(self.grid[r]))
            if r < self.n - 1:
                print("-" * (self.n * 4 - 3))

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

class NetworkGame:
    def __init__(self, n=3):
        self.board = Board(n)
        self.players = []
        self.clients = []
        self.current_turn = 0
        
    def add_client(self, client_socket, player_name, symbol):
        player = Player(player_name, symbol)
        self.players.append(player)
        self.clients.append(client_socket)
        
    def broadcast_board(self):
        board_str = f"BOARD|{self.board.n}|"
        for row in self.board.grid:
            board_str += ",".join(row) + "|"
        message = board_str.rstrip("|") + '\n'
        for client in self.clients:
            try:
                client.send(message.encode())
            except:
                pass
                
    def send_to_client(self, client_index, message_type, data=""):
        message = f"{message_type}|{data}\n"
        try:
            self.clients[client_index].send(message.encode())
        except:
            pass
            
    def play_networked(self):
        self.broadcast_board()
        
        while True:
            current_player = self.players[self.current_turn % 2]
            current_client = self.clients[self.current_turn % 2]
            
            self.send_to_client(self.current_turn % 2, "YOUR_TURN", f"{current_player.symbol}|{current_player.name}")
            
            other_player_index = (self.current_turn + 1) % 2
            self.send_to_client(other_player_index, "WAIT_TURN", current_player.name)
            
            try:
                data = current_client.recv(1024).decode().strip()
                parts = data.split("|")
                if len(parts) == 3 and parts[0] == "MOVE":
                    row = int(parts[1])
                    col = int(parts[2])
                
                    if self.board.place(row, col, current_player.symbol):
                        self.broadcast_board()
                        
                        if self.board.check_win(current_player.symbol):
                            for client in self.clients:
                                self.send_to_client(self.clients.index(client), "GAME_OVER", f"WIN|{current_player.name}")
                            break
                            
                        if self.board.full():
                            for client in self.clients:
                                self.send_to_client(self.clients.index(client), "GAME_OVER", "DRAW")
                            break
                            
                        self.current_turn += 1
                    else:
                        self.send_to_client(self.current_turn % 2, "INVALID_MOVE", "Invalid move, try again")
                    
            except Exception:
                print("Error in connection")
                break

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    host = "0.0.0.0"#pls enter the ipv4 address
    port = 9999
    
    server.bind((host, port))
    server.listen(2)
    print(f"Server listening on {host}:{port}")
    print("Waiting for 2 players to connect")
    
    game = NetworkGame(3)
    clients = []
    
    for i in range(2):
        client_socket, addr = server.accept()
        clients.append(client_socket)
        
        player_num = i + 1
        print(f"Player {player_num} connected from {addr}")
        
        player_info = f"PLAYER_INFO|{player_num}|{'X' if player_num == 1 else 'O'}|Player {player_num}\n"
        client_socket.send(player_info.encode())
        
        game.add_client(client_socket, f'Player {player_num}', 'X' if player_num == 1 else 'O')
        
    print("Starting game")
    
    try:
        game.play_networked()
    except Exception:
        print("Game error")
    
    for client in clients:
        client.close()
    server.close()
    print("Server closed")

start_server()