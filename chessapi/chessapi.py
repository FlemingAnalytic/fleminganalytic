from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import chess
import chess.engine
import chess.pgn
import uuid
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import io
import random  # Added for DB probability
import os  # Added for PGN file check
from contextlib import contextmanager

from apps.session_store import SessionStore, SessionConflict

# Piece-Square Table definitions (from Stockfish-like evaluations)
# All tables are defined for White's pieces.
pawn_table = (
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, -20, -20, 10, 10, 5,
    5, -5, -10, 0, 0, -10, -5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, 5, 10, 25, 25, 10, 5, 5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
    0, 0, 0, 0, 0, 0, 0, 0
)

knight_table = (
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
)

bishop_table = (
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20
)

rook_table = (
    0, 0, 0, 5, 5, 0, 0, 0,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    5, 10, 10, 10, 10, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0
)

queen_table = (
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 5, 5, 5, 5, 5, 5, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20
)

king_table_middle = (
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20
)

# Helper map to link piece type to its table
PST_MAP = {
    chess.PAWN: pawn_table,
    chess.KNIGHT: knight_table,
    chess.BISHOP: bishop_table,
    chess.ROOK: rook_table,
    chess.QUEEN: queen_table,
    chess.KING: king_table_middle,
}

# Global Transposition Table for caching engine results
# Key: FEN string, Value: (score, depth)
transposition_table: Dict[str, tuple[float, int]] = {}

router = APIRouter(
    prefix="",
    tags=["Chess API"],
)

# Session expiration time (1 hour)
SESSION_EXPIRATION_HOURS = 1

# Game sessions live in SQLite, not in this process's memory.
#
# They used to be a module-global dict, which meant a game only existed inside
# the one worker that created it. That is why the whole domain ran at
# `workers = 1`: with a second worker, every other move would 404 because it
# landed on the process that had never heard of the game.
#
# The board is stored as its move list and replayed on load, not as a FEN.
# A FEN describes a position, not how it was reached, so restoring from one
# would silently break threefold repetition and the fifty-move rule - the game
# would still look right and would draw incorrectly.
game_sessions = SessionStore("chess", ttl_seconds=SESSION_EXPIRATION_HOURS * 3600)


def _hydrate(data: dict) -> dict:
    """Stored JSON -> a live session with a real chess.Board."""
    board = chess.Board()
    for uci in data.get("moves_uci", []):
        board.push(chess.Move.from_uci(uci))
    session = dict(data)
    session["board"] = board
    session["created_at"] = datetime.fromisoformat(data["created_at"])
    session["last_activity"] = datetime.fromisoformat(data["last_activity"])
    return session


def _dehydrate(session: dict) -> dict:
    """A live session -> JSON-safe storage form."""
    board = session["board"]
    return {
        "moves_uci": [m.uci() for m in board.move_stack],
        "player_color": session["player_color"],
        "ai_difficulty": session["ai_difficulty"],
        "move_history": session["move_history"],
        "created_at": session["created_at"].isoformat(),
        "last_activity": datetime.now().isoformat(),
        "status": session["status"],
    }


@contextmanager
def open_game(session_id: str):
    """Load a game, let the handler play into it, save it back on a clean exit.

    A handler that raises writes nothing, so a rejected move cannot leave the
    board half-updated.
    """
    try:
        with game_sessions.checkout(session_id) as data:
            session = _hydrate(data)
            yield session
            data.clear()
            data.update(_dehydrate(session))
    except KeyError:
        raise HTTPException(status_code=404, detail="Game session not found")
    except SessionConflict:
        # Two moves for the same game arrived at once - a double-click, or the
        # same game open in two tabs. Saying so is better than quietly losing
        # one of them, which is what the old shared dict did.
        raise HTTPException(
            status_code=409,
            detail="That game was updated by another request. Reload the board and try again.",
        )


def read_game(session_id: str) -> dict:
    """Load a game read-only. Use open_game if you intend to change it."""
    data = game_sessions.get(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Game session not found")
    return _hydrate(data)

# Enhanced ChessMoveDatabase class with move statistics and win rates
class ChessMoveDatabase:
    """
    Enhanced chess move recommendation library with move statistics and win rates.
    Key: FEN (str), Value: Dict[uci_move (str), Dict[str, int]] containing move statistics.
    """
    
    def __init__(self, database=None):
        """
        Initialize the database.
        :param database: Optional dict. If None, uses a small hardcoded database.
        """
        # Key: FEN (str), Value: Dict[uci_move (str), Dict[str, int]]
        self._database: dict[str, dict[str, dict[str, int]]] = database if database is not None else {}
        if not self._database:
            self._load_hardcoded_database()
    
    def _add_move_stat(self, fen: str, uci_move: str, result: str):
        """Internal helper to update move statistics."""
        if fen not in self._database:
            self._database[fen] = {}
        if uci_move not in self._database[fen]:
            self._database[fen][uci_move] = {'count': 0, 'wins': 0, 'draws': 0, 'losses': 0}
            
        stats = self._database[fen][uci_move]
        stats['count'] += 1
        
        # Determine the color whose turn it was
        board_temp = chess.Board(fen)
        is_white_move = board_temp.turn == chess.WHITE

        if result == '1-0':
            stats['wins'] += 1 if is_white_move else 0
            stats['losses'] += 1 if not is_white_move else 0
        elif result == '0-1':
            stats['losses'] += 1 if is_white_move else 0
            stats['wins'] += 1 if not is_white_move else 0
        elif result == '1/2-1/2':
            stats['draws'] += 1
    
    def _load_hardcoded_database(self):
        """Load a small hardcoded database with basic opening moves."""
        # Starting position: e4 (King's Pawn Opening)
        start_fen = chess.Board().fen()
        self._add_move_stat(start_fen, "e2e4", "1-0")  # Simulate some wins
        self._add_move_stat(start_fen, "e2e4", "1-0")
        self._add_move_stat(start_fen, "e2e4", "1/2-1/2")
        self._add_move_stat(start_fen, "d2d4", "1-0")
        self._add_move_stat(start_fen, "d2d4", "1/2-1/2")
        
        # After e4: e5 (Open Game)
        board_after_e4 = chess.Board(start_fen)
        board_after_e4.push_uci("e2e4")
        self._add_move_stat(board_after_e4.fen(), "e7e5", "0-1")
        self._add_move_stat(board_after_e4.fen(), "e7e5", "1/2-1/2")
        self._add_move_stat(board_after_e4.fen(), "c7c5", "0-1")  # Sicilian
        
        # After e4 e5: Nf3 (Ruy Lopez setup)
        board_after_e4e5 = board_after_e4.copy()
        board_after_e4e5.push_uci("e7e5")
        self._add_move_stat(board_after_e4e5.fen(), "g1f3", "1-0")
        self._add_move_stat(board_after_e4e5.fen(), "g1f3", "1/2-1/2")
    
    def load_from_pgn(self, pgn_file_path: str):
        """
        Load moves from a PGN file, recording count and win/loss statistics.
        This processes ALL moves in the mainline of ALL games.
        """
        print(f"Loading PGN data from: {pgn_file_path}...")
        try:
            with open(pgn_file_path, 'r', encoding='utf-8') as pgn_file:
                while True:
                    game = chess.pgn.read_game(pgn_file)
                    if game is None:
                        break
                        
                    # Get the game result (e.g., '1-0', '0-1', '1/2-1/2')
                    result = game.headers.get("Result")
                    if not result:
                        continue  # Skip games without a result

                    board = game.board()
                    for move in game.mainline_moves():
                        fen_before = board.fen()
                        self._add_move_stat(fen_before, move.uci(), result)
                        board.push(move)
            print("PGN loading complete.")
        except FileNotFoundError:
            print(f"Error: PGN file not found at {pgn_file_path}")
        except Exception as e:
            print(f"An error occurred during PGN processing: {e}")

    def get_best_move(self, board: chess.Board, strategy: str = 'win_rate') -> Optional[str]:
        """
        Get the best recommended move based on a strategy.
        :param board: A chess.Board object.
        :param strategy: 'win_rate' (highest expected score) or 'count' (most popular).
        :return: str UCI move if found, else None.
        """
        fen = board.fen()
        if fen not in self._database:
            return None
        
        move_stats = self._database[fen]
        best_move_uci = None
        best_score = float('-inf')

        for uci_move, stats in move_stats.items():
            # Check legality before considering
            try:
                move = chess.Move.from_uci(uci_move)
                if move not in board.legal_moves:
                    continue
            except ValueError:
                continue  # Skip invalid UCI strings
            
            count = stats['count']
            if count < 3:  # Threshold for reliable statistics
                continue

            current_score = 0.0
            
            if strategy == 'win_rate':
                # Expected Score = (Wins * 1.0 + Draws * 0.5) / Count
                current_score = (stats['wins'] * 1.0 + stats['draws'] * 0.5) / count
            elif strategy == 'count':
                # Pure popularity
                current_score = count

            if current_score > best_score:
                best_score = current_score
                best_move_uci = uci_move
                
        return best_move_uci

# NEW: Global DB instance (initialize once on startup)
move_db = ChessMoveDatabase()
# Load a real DB if available (e.g., place 'openings.pgn' in the same directory)
if os.path.exists('openings.pgn'):
    move_db.load_from_pgn('openings.pgn')

# Global storage for parsed games (for auto-replay feature)
parsed_games = []
games_loaded = False

def load_games_for_replay(pgn_file_path='chessapi/openings.pgn', max_games=5000):
    """
    Load and index games from PGN file for auto-replay feature.
    Stores game metadata and moves.
    """
    global parsed_games, games_loaded

    if games_loaded:
        return

    print(f"Loading games from {pgn_file_path} for replay feature...")
    try:
        with open(pgn_file_path, 'r', encoding='utf-8') as pgn_file:
            game_count = 0
            while game_count < max_games:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break

                # Extract game metadata
                headers = game.headers
                moves = []
                board = game.board()

                # Extract all moves
                for move in game.mainline_moves():
                    san = board.san(move)
                    fen_before = board.fen()
                    board.push(move)
                    fen_after = board.fen()

                    moves.append({
                        'san': san,
                        'uci': move.uci(),
                        'fen_before': fen_before,
                        'fen_after': fen_after
                    })

                # Store game data
                parsed_games.append({
                    'id': game_count,
                    'white': headers.get('White', 'Unknown'),
                    'black': headers.get('Black', 'Unknown'),
                    'event': headers.get('Event', 'Unknown'),
                    'date': headers.get('Date', 'Unknown'),
                    'result': headers.get('Result', '*'),
                    'white_elo': headers.get('WhiteElo', 'N/A'),
                    'black_elo': headers.get('BlackElo', 'N/A'),
                    'moves': moves,
                    'move_count': len(moves)
                })

                game_count += 1

                if game_count % 100 == 0:
                    print(f"Loaded {game_count} games...")

        games_loaded = True
        print(f"✓ Loaded {len(parsed_games)} games for replay")

    except FileNotFoundError:
        print(f"Warning: {pgn_file_path} not found. Auto-replay feature disabled.")
    except Exception as e:
        print(f"Error loading games: {e}")

# Load games on startup
load_games_for_replay()

def cleanup_expired_sessions():
    """Drop games untouched for more than SESSION_EXPIRATION_HOURS.

    The store already refuses to return an expired session, so this is only
    reclaiming disk. It no longer has to walk every game in memory to do it.
    """
    return game_sessions.purge_expired()

def update_session_activity(session_id: str):
    """Push the expiry out. A cheap UPDATE - it does not rewrite the board."""
    game_sessions.touch(session_id)

# Pydantic models for API requests/responses
class NewGameRequest(BaseModel):
    player_color: Optional[str] = Field(default="white", description="Player color: 'white' or 'black'")
    ai_difficulty: Optional[int] = Field(default=1, description="AI difficulty level 1-5", ge=1, le=5)

class MoveRequest(BaseModel):
    session_id: str = Field(description="Game session ID")
    move: str = Field(description="Move in algebraic notation (e.g., 'e2e4', 'Nf3', 'O-O')")

class GetMoveRequest(BaseModel):
    session_id: str = Field(description="Game session ID")

class HintRequest(BaseModel):
    session_id: str = Field(description="Game session ID")

class GameState(BaseModel):
    session_id: str
    board_fen: str
    current_player: str
    game_status: str
    move_history: List[str]
    is_check: bool
    is_checkmate: bool
    is_stalemate: bool
    is_draw: bool
    legal_moves: List[str]
    last_move: Optional[str]
    captured_pieces: Dict[str, List[str]]
    suggested_next_move: Optional[str]
    move_explanation: Optional[str]
    pieces_under_attack: Optional[List[str]] = None  # List of squares with pieces under attack

class MoveResponse(BaseModel):
    success: bool
    game_state: GameState
    message: str
    ai_move: Optional[str] = None
    ai_from_square: Optional[str] = None  # NEW: For flash animation
    ai_to_square: Optional[str] = None    # NEW: For flash animation

def parse_move_notation(move_str: str, board: chess.Board) -> chess.Move:
    """
    Parse move notation efficiently, prioritizing standard formats.
    """
    original_move_str = move_str.strip()
    
    # 1. Handle Castling (O-O, 0-0, O-O-O, 0-0-0)
    # The board.parse_san() typically handles 'O-O' and 'O-O-O', but
    # explicit handling for variations (like '0-0') and full commands
    move_str_lower = original_move_str.lower().replace('-', '').replace(' ', '')
    
    if move_str_lower in ['oo', '00', 'castlekingside']:
        return board.parse_san('O-O')
    if move_str_lower in ['ooo', '000', 'castlequeenside']:
        return board.parse_san('O-O-O')
    
    # 2. Try Standard Algebraic Notation (SAN)
    # This handles Nf3, Qe7, e4, captures (exf5), and promotions (e8Q).
    # The board's parse_san is very robust.
    try:
        return board.parse_san(original_move_str)
    except ValueError:
        pass  # Fall through to other checks

    # 3. Try Universal Chess Interface (UCI)
    # This handles the unambiguous e2e4, g1f3, a7a8q, etc.
    move_str_clean = move_str_lower.replace(' ', '')
    if len(move_str_clean) >= 4 and len(move_str_clean) <= 5:
        try:
            move = chess.Move.from_uci(move_str_clean)
            if move in board.legal_moves:
                return move
        except ValueError:
            pass  # Fall through
    
    # 4. Flexible/Friendly Parsing (The custom logic)
    # Try the "from-to" format (e.g., "g1 f3" or "e2 e4")
    parts = original_move_str.lower().split()
    if len(parts) == 2 and len(parts[0]) == 2 and len(parts[1]) == 2:
        try:
            # Combine into UCI (e.g., 'g1f3')
            uci_move = parts[0] + parts[1]
            move = chess.Move.from_uci(uci_move)
            if move in board.legal_moves:
                return move
        except:
            pass
            
    # Try a simple cleanup of the original string and re-test SAN/UCI
    # (e.g. for input "Q E 7" which failed the first SAN test)
    move_str_compacted = "".join(parts) if parts else original_move_str.replace(' ', '')
    if move_str_compacted:
        try:
            return board.parse_san(move_str_compacted)
        except ValueError:
            pass

    # If all parsing fails, raise an informative error
    raise ValueError(
        f"Invalid move notation: {original_move_str}. "
        "Try Standard Algebraic (e.g., 'Qe7', 'Nf3', 'O-O') or UCI (e.g., 'e2e4')."
    )

# MODIFIED: Enhanced get_move_explanation to handle DB moves
def get_move_explanation(board: chess.Board, suggested_move: str, is_db_move: bool = False) -> str:
    if not suggested_move:
        return "No legal moves available."
    try:
        move = board.parse_san(suggested_move)
        piece = board.piece_at(move.from_square)
        if not piece:
            return "Invalid move position."
        
        piece_name = chess.piece_name(piece.piece_type).capitalize()
        from_square = chess.square_name(move.from_square)
        to_square = chess.square_name(move.to_square)
        
        # Special case for castling
        if board.is_castling(move):
            side = "kingside" if move.to_square > move.from_square else "queenside"
            base_exp = f"Castles {side} (O-O{'O' if side == 'queenside' else ''}), moving the king to safety and activating the rook."
        else:
            explanations = []
            
            # Check for captures
            is_capture = board.is_capture(move)
            if is_capture:
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    captured_name = chess.piece_name(captured_piece.piece_type)
                    explanations.append(f"captures {captured_name} on {to_square}")
            
            # Make the move temporarily to analyze the position
            board.push(move)
            
            # Check if it gives check
            gives_check = board.is_check()
            if gives_check:
                explanations.append("gives check")
            
            # Analyze what pieces this move now attacks
            attacked_pieces = []
            for target_square in chess.SQUARES:
                target_piece = board.piece_at(target_square)
                if target_piece and target_piece.color != piece.color:
                    # Check if our moved piece attacks this square
                    if board.is_attacked_by(piece.color, target_square):
                        # Verify it's actually from our moved piece by checking if the square is in attack range
                        attackers = board.attackers(piece.color, target_square)
                        if move.to_square in attackers:  # attackers is a SquareSet (set of square integers)
                            attacked_pieces.append(f"{chess.piece_name(target_piece.piece_type)} on {chess.square_name(target_square)}")
            
            if attacked_pieces and len(attacked_pieces) <= 3:
                explanations.append(f"attacks {', '.join(attacked_pieces)}")
            elif len(attacked_pieces) > 3:
                explanations.append(f"attacks multiple enemy pieces ({len(attacked_pieces)} pieces)")
            
            # Analyze what pieces this move now defends (only report if piece was previously undefended and under attack)
            defended_pieces = []
            
            # First, undo the move to check the previous position
            board.pop()
            
            for target_square in chess.SQUARES:
                target_piece = board.piece_at(target_square)
                if target_piece and target_piece.color == piece.color and target_square != move.to_square:
                    # Check if this piece was under attack in the previous position
                    was_under_attack = board.is_attacked_by(not piece.color, target_square)
                    if was_under_attack:
                        # Count how many defenders it had before the move
                        old_defenders = len(board.attackers(piece.color, target_square))
                        
                        # Now check after the move
                        board.push(move)
                        new_defenders = len(board.attackers(piece.color, target_square))
                        is_our_piece_defending = move.to_square in board.attackers(piece.color, target_square)
                        board.pop()
                        
                        # Only report as "defended" if:
                        # 1. Our piece is now defending it AND
                        # 2. It was previously undefended (0 defenders) or under-defended and still under attack
                        if is_our_piece_defending and (old_defenders == 0 or (old_defenders < 2 and new_defenders > old_defenders)):
                            defended_pieces.append(f"{chess.piece_name(target_piece.piece_type)} on {chess.square_name(target_square)}")
            
            # Restore the move for the rest of the analysis
            board.push(move)
            
            if defended_pieces and len(defended_pieces) <= 2:
                explanations.append(f"defends {', '.join(defended_pieces)}")
            elif len(defended_pieces) > 2:
                explanations.append(f"defends {len(defended_pieces)} allied pieces")
            
            board.pop()  # Undo the move
            
            # Check if this move was to escape an attack
            if board.is_attacked_by(not piece.color, move.from_square):
                explanations.append(f"moves to safety from {from_square}")
            
            # Promotion
            if move.promotion:
                promotion_piece = chess.piece_name(move.promotion)
                explanations.insert(0, f"promotes to {promotion_piece}")
            
            # Positional considerations
            if not explanations:
                # Center control
                if move.to_square in [27, 28, 35, 36]:  # e4, d4, e5, d5
                    explanations.append("controls the center")
                # Development in opening
                elif len(board.move_stack) < 15:
                    if piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                        explanations.append("develops a piece")
                    elif piece.piece_type == chess.PAWN and move.to_square in [27, 28, 35, 36]:
                        explanations.append("establishes central pawn presence")
                # Advanced position
                if piece.piece_type != chess.KING and piece.piece_type != chess.PAWN:
                    from_rank = chess.square_rank(move.from_square)
                    to_rank = chess.square_rank(move.to_square)
                    if piece.color == chess.WHITE and to_rank > from_rank:
                        explanations.append("advances forward")
                    elif piece.color == chess.BLACK and to_rank < from_rank:
                        explanations.append("advances forward")
            
            # Build base explanation
            if explanations:
                base_exp = f"{piece_name} to {to_square}: " + ", ".join(explanations) + "."
            else:
                base_exp = f"{piece_name} to {to_square} - improves position."
        
        # NEW: Add DB rationale if applicable
        if is_db_move:
            base_exp += " (standard book move from opening theory, high win rate in GM games)."
        
        return base_exp
    except Exception as e:
        return f"Suggested move {suggested_move} - a strong continuation in this position."

def get_captured_pieces(board: chess.Board) -> Dict[str, List[str]]:
    piece_counts = {'p': 8, 'r': 2, 'n': 2, 'b': 2, 'q': 1, 'k': 1}
    current_pieces = [board.piece_at(sq).symbol().lower() if board.piece_at(sq) else None for sq in chess.SQUARES]
    current_pieces = [p for p in current_pieces if p is not None]
    
    captured_by_white = []
    captured_by_black = []
    
    for piece_type in piece_counts:
        current_white = sum(1 for p in current_pieces if p.upper() == piece_type.upper())
        current_black = sum(1 for p in current_pieces if p == piece_type)
        
        missing_white = piece_counts[piece_type] - current_white
        missing_black = piece_counts[piece_type] - current_black
        
        captured_by_white.extend([piece_type.upper()] * missing_white)  # Black pieces captured by white
        captured_by_black.extend([piece_type] * missing_black)  # White pieces captured by black
    
    return {
        "captured_by_white": captured_by_white,
        "captured_by_black": captured_by_black
    }

def get_pieces_under_attack(board: chess.Board, player_color: str) -> List[str]:
    """
    Find all pieces of the current player that are under attack by the opponent.
    Returns a list of square names (e.g., ['e4', 'f3'])
    """
    pieces_under_attack = []
    color = chess.WHITE if player_color == 'white' else chess.BLACK
    opponent_color = not color

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        # Check if it's our piece and if opponent is attacking it
        if piece and piece.color == color:
            if board.is_attacked_by(opponent_color, square):
                # Check if the piece is defended
                is_defended = board.is_attacked_by(color, square)
                # Only highlight if it's not defended OR if the attacker is less valuable
                # For simplicity, we'll highlight all attacked pieces to help beginners
                pieces_under_attack.append(chess.square_name(square))

    return pieces_under_attack

def create_game_state(session_id: str, board: chess.Board, last_move: Optional[str] = None, session_data: Optional[dict] = None) -> GameState:
    # Strip check/checkmate symbols from legal moves
    legal_moves = [board.san(move).replace('+', '').replace('#', '') for move in board.legal_moves]
    suggested_move = None
    explanation = None
    if not board.is_game_over() and legal_moves:
        ai_difficulty = 3
        if session_data:
            ai_difficulty = session_data.get("ai_difficulty", 3)
        suggested_move, is_db = get_ai_move(board, ai_difficulty)  # MODIFIED: Now returns (move, is_db)
        explanation = get_move_explanation(board, suggested_move, is_db)
    elif board.is_game_over():
        if board.is_checkmate():
            winner = "Black" if board.turn == chess.WHITE else "White"
            explanation = f"Game over: {winner} wins by checkmate!"
        elif board.is_stalemate():
            explanation = "Game over: Stalemate - it's a draw!"
        elif board.is_insufficient_material():
            explanation = "Game over: Draw due to insufficient material."
        else:
            explanation = "Game over."
    # Get pieces under attack for the HUMAN player (not just current turn)
    current_player_color = "white" if board.turn == chess.WHITE else "black"

    # Check pieces under attack for the human player specifically
    if session_data:
        player_color = session_data.get("player_color", "white")
        pieces_under_attack = get_pieces_under_attack(board, player_color)
    else:
        # Fallback: check for current player
        pieces_under_attack = get_pieces_under_attack(board, current_player_color)

    return GameState(
        session_id=session_id,
        board_fen=board.fen(),
        current_player=current_player_color,
        game_status="active" if not board.is_game_over() else "finished",
        move_history=[],  # Will be set later
        is_check=board.is_check(),
        is_checkmate=board.is_checkmate(),
        is_stalemate=board.is_stalemate(),
        is_draw=board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition(),
        legal_moves=legal_moves,
        last_move=last_move,
        captured_pieces=get_captured_pieces(board),
        suggested_next_move=suggested_move,
        move_explanation=explanation,
        pieces_under_attack=pieces_under_attack
    )

# MODIFIED: Enhanced get_ai_move with DB integration and better evaluation
def get_ai_move(board: chess.Board, difficulty: int = 1) -> tuple[Optional[str], bool]:
    """
    Get AI move with improved evaluation, returns (san_move, is_db_move).
    """
    if board.is_game_over():
        return None, False
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None, False
    
    # Database lookup for known positions (openings) - use more for higher difficulty
    db_uci = move_db.get_best_move(board)
    is_db_move = False
    if db_uci:
        db_move = chess.Move.from_uci(db_uci)
        if db_move in legal_moves:
            # Higher difficulty should use book moves more often (they're usually good)
            use_db_prob = min(0.9, 0.3 + (difficulty - 1) * 0.15)  # e.g., 0.3 at lvl1, 0.9 at lvl5
            if random.random() < use_db_prob:
                san_move = board.san(db_move)
                is_db_move = True
                return san_move, is_db_move
    
    # Difficulty-based move selection
    if difficulty == 1:
        # Level 1: Random moves with slight preference for captures
        captures = [move for move in legal_moves if board.is_capture(move)]
        if captures and random.random() < 0.3:  # 30% chance to prefer captures
            move = random.choice(captures)
        else:
            move = random.choice(legal_moves)
    elif difficulty == 2:
        # Level 2: Simple evaluation without deep search
        move = get_best_move_simple(board, legal_moves)
    elif difficulty == 3:
        # Level 3: Minimax depth 2
        move = minimax_search(board, depth=2)
    elif difficulty == 4:
        # Level 4: Minimax depth 3
        move = minimax_search(board, depth=3)
    else:
        # Level 5: Minimax depth 4
        move = minimax_search(board, depth=4)
    
    return board.san(move), is_db_move

def get_best_move_simple(board: chess.Board, legal_moves: list) -> chess.Move:
    """
    Simple move evaluation for difficulty level 2 - looks for obvious good moves.
    """
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        score = 0
        
        # Heavily favor captures
        if board.is_capture(move):
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                material_values = {
                    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
                    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
                }
                score += material_values.get(captured_piece.piece_type, 0)
        
        # Check for checkmate
        board.push(move)
        if board.is_checkmate():
            score += 10000
        elif board.is_check():
            score += 50
        board.pop()
        
        # Avoid moving into danger
        if board.is_attacked_by(not board.turn, move.to_square):
            moving_piece = board.piece_at(move.from_square)
            if moving_piece:
                material_values = {
                    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
                    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
                }
                score -= material_values.get(moving_piece.piece_type, 0) * 0.5
        
        # Add some randomness
        score += random.uniform(-10, 10)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move if best_move else random.choice(legal_moves)

def evaluate_move_simple(board: chess.Board, move: chess.Move) -> float:
    """
    Simple evaluation for a move - considers captures and checks.
    Returns a score for the move.
    """
    score = 0.0
    
    # Evaluate capture
    if board.is_capture(move):
        captured_piece = board.piece_at(move.to_square)
        if captured_piece:
            material_values = {
                chess.PAWN: 100,
                chess.KNIGHT: 320,
                chess.BISHOP: 330,
                chess.ROOK: 500,
                chess.QUEEN: 900,
                chess.KING: 0
            }
            score += material_values.get(captured_piece.piece_type, 0)
            
            # Bonus for capturing with lower value piece
            moving_piece = board.piece_at(move.from_square)
            if moving_piece:
                score += material_values.get(captured_piece.piece_type, 0) - material_values.get(moving_piece.piece_type, 0) * 0.1
    
    # Make move to check for check/checkmate
    board.push(move)
    
    # Big bonus for checkmate
    if board.is_checkmate():
        score += 10000
    # Bonus for check
    elif board.is_check():
        score += 50
    
    board.pop()
    
    return score

def minimax_search(board: chess.Board, depth: int) -> chess.Move:
    """
    Minimax search with alpha-beta pruning for better move selection.
    """
    best_move = None
    best_value = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    # We're maximizing for the current player (whose turn it is)
    for move in board.legal_moves:
        board.push(move)
        # After making our move, it's the opponent's turn (minimizing)
        value = minimax(board, depth - 1, alpha, beta, False)
        board.pop()
        
        if value > best_value:
            best_value = value
            best_move = move
        
        alpha = max(alpha, value)
        if beta <= alpha:
            break  # Alpha-beta pruning
    
    return best_move if best_move else random.choice(list(board.legal_moves))

def minimax(board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """
    Minimax algorithm with alpha-beta pruning and Transposition Table lookup.
    """
    fen = board.fen()
    
    # 1. Transposition Table Lookup
    if fen in transposition_table:
        stored_score, stored_depth = transposition_table[fen]
        # Only use the stored result if it was calculated at the current depth or deeper
        if stored_depth >= depth:
            return stored_score

    # Base Case: Depth limit reached or game over
    if depth == 0 or board.is_game_over():
        score = evaluate_position_advanced(board)
        # Store base case evaluation
        transposition_table[fen] = (score, depth)
        return score
    
    # Standard Minimax Logic
    if maximizing:
        max_eval = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        
        # 2. Store Result in TT
        transposition_table[fen] = (max_eval, depth)
        return max_eval
        
    else:  # Minimizing
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        
        # 2. Store Result in TT
        transposition_table[fen] = (min_eval, depth)
        return min_eval

def evaluate_position_advanced(board: chess.Board) -> float:
    """
    Advanced position evaluation with material and Piece-Square Tables (PSTs).
    Returns positive values for positions favoring the current player to move.
    """
    if board.is_checkmate():
        return -99999  # Current player is checkmated (very bad)
    
    if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition():
        return 0
    
    material_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }
    
    current_player = board.turn
    score = 0
    
    # Material and positional evaluation using PSTs
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            piece_type = piece.piece_type
            
            # 1. Material Evaluation
            value = material_values[piece_type]
            
            # 2. Positional Evaluation (PST)
            pst_table = PST_MAP[piece_type]
            
            if piece.color == chess.WHITE:
                # White uses the table directly
                pst_value = pst_table[square]
            else:
                # Black uses the flipped table (mirroring across the 4th/5th rank)
                flipped_square = chess.square_mirror(square)
                pst_value = pst_table[flipped_square]
            
            # Combine material and positional score
            total_value = value + pst_value
            
            # Adjust score relative to the current player
            if piece.color == current_player:
                score += total_value
            else:
                score -= total_value
    
    # 3. Mobility Bonus (gives a small reward for having more legal moves)
    mobility_factor = 0.5  # Points per legal move
    score += len(list(board.legal_moves)) * mobility_factor
    
    # 4. Penalty for being in check
    if board.is_check():
        score -= 50
    
    return score

def evaluate_position(board: chess.Board) -> float:
    if board.is_checkmate():
        return -9999 if board.turn else 9999
    material_values = {
        chess.PAWN: 1,
        chess.ROOK: 5,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = material_values[piece.piece_type]
            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value
    return score

@router.post("/new_game", response_model=GameState)
async def new_game(request: NewGameRequest):
    # Clean up expired sessions before creating new one
    cleanup_expired_sessions()
    
    # Clear the Transposition Table for a new game
    global transposition_table
    transposition_table.clear()
    
    session_id = str(uuid.uuid4())
    board = chess.Board()
    game_session = {
        "board": board,
        "player_color": request.player_color.lower(),
        "ai_difficulty": request.ai_difficulty,
        "move_history": [],
        "created_at": datetime.now(),
        "last_activity": datetime.now(),
        "status": "active"
    }
    game_sessions.create(session_id, _dehydrate(game_session))
    game_state = create_game_state(session_id, board, session_data=game_session)
    game_state.move_history = game_session["move_history"]
    return game_state

@router.post("/make_move", response_model=MoveResponse)
async def make_move(request: MoveRequest):
    with open_game(request.session_id) as session:
        board = session["board"]
        if board.is_game_over():
            raise HTTPException(status_code=400, detail="Game is already over")
        try:
            move = parse_move_notation(request.move, board)
            if move not in board.legal_moves:
                raise HTTPException(status_code=400, detail=f"Illegal move: {request.move}")
            san_move = board.san(move)
            board.push(move)
            session["move_history"].append(san_move)
            game_state = create_game_state(request.session_id, board, san_move, session)
            game_state.move_history = session["move_history"]
            ai_move = None
            ai_from_square = None
            ai_to_square = None
            message = f"Move {san_move} played successfully"
            if board.is_game_over():
                if board.is_checkmate():
                    winner = "Black" if board.turn == chess.WHITE else "White"
                    message += f". Checkmate! {winner} wins!"
                    session["status"] = "finished"
                elif board.is_stalemate():
                    message += ". Stalemate! It's a draw."
                    session["status"] = "finished"
                elif board.is_insufficient_material():
                    message += ". Draw due to insufficient material."
                    session["status"] = "finished"
            else:
                current_player_color = "white" if board.turn == chess.WHITE else "black"
                if current_player_color != session["player_color"]:
                    ai_move_san, _ = get_ai_move(board, session["ai_difficulty"])  # MODIFIED: Ignore is_db here
                    if ai_move_san:
                        try:
                            ai_move_obj = board.parse_san(ai_move_san)

                            # Extract from/to squares before pushing (for flash animation)
                            ai_from_square = chess.square_name(ai_move_obj.from_square)
                            ai_to_square = chess.square_name(ai_move_obj.to_square)

                            board.push(ai_move_obj)
                            session["move_history"].append(ai_move_san)
                            ai_move = ai_move_san
                            message += f". AI played {ai_move_san}"
                            game_state = create_game_state(request.session_id, board, ai_move_san, session)
                            game_state.move_history = session["move_history"]
                            if board.is_game_over():
                                if board.is_checkmate():
                                    winner = "Black" if board.turn == chess.WHITE else "White"
                                    message += f". Checkmate! {winner} wins!"
                                    session["status"] = "finished"
                                elif board.is_stalemate():
                                    message += ". Stalemate! It's a draw."
                                    session["status"] = "finished"
                        except Exception as e:
                            message += f". AI move failed: {str(e)}"
            return MoveResponse(
                success=True,
                game_state=game_state,
                message=message,
                ai_move=ai_move,
                ai_from_square=ai_from_square,
                ai_to_square=ai_to_square
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error making move: {str(e)}")

# MODIFIED: /get_ai_move endpoint to include is_db_move
@router.post("/get_ai_move")
async def get_ai_move_endpoint(request: GetMoveRequest):
    with open_game(request.session_id) as session:
        board = session["board"]

        if board.is_game_over():
            raise HTTPException(status_code=400, detail="Game is already over")

        current_player_color = "white" if board.turn == chess.WHITE else "black"
        player_color = session["player_color"]

        if current_player_color == player_color:
            raise HTTPException(
                status_code=400, 
                detail=f"It's the human player's turn ({current_player_color}), not the AI's turn. The AI plays {('black' if player_color == 'white' else 'white')}."
            )

        ai_move_san, is_db_move = get_ai_move(board, session["ai_difficulty"])
        if not ai_move_san:
            raise HTTPException(status_code=400, detail="No legal moves available")

        # Actually make the AI move on the board
        try:
            ai_move_obj = board.parse_san(ai_move_san)

            # Get from/to squares before pushing the move (for flash animation)
            from_square = chess.square_name(ai_move_obj.from_square)
            to_square = chess.square_name(ai_move_obj.to_square)

            board.push(ai_move_obj)
            session["move_history"].append(ai_move_san)

            # Check if game is over after AI move
            game_over = board.is_game_over()
            checkmate = board.is_checkmate()
            stalemate = board.is_stalemate()
            draw = board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition()

            if game_over:
                session["status"] = "finished"

            # Create updated game state
            game_state = create_game_state(request.session_id, board, ai_move_san, session)
            game_state.move_history = session["move_history"]

            return {
                "ai_move": ai_move_san,
                "from_square": from_square,  # NEW: For flash animation
                "to_square": to_square,      # NEW: For flash animation
                "is_db_move": is_db_move,
                "session_id": request.session_id,
                "ai_color": "black" if player_color == "white" else "white",
                "current_turn": "white" if board.turn == chess.WHITE else "black",
                "game_over": game_over,
                "checkmate": checkmate,
                "stalemate": stalemate,
                "draw": draw,
                "game_state": game_state
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error making AI move: {str(e)}")

@router.post("/get_hint")
async def get_hint(request: HintRequest):
    # Read-only: a hint suggests a move, it does not play one.
    session = read_game(request.session_id)
    board = session["board"]
    if board.is_game_over():
        raise HTTPException(status_code=400, detail="Game is already over")
    current_player_color = "white" if board.turn == chess.WHITE else "black"
    player_color = session["player_color"]
    suggested_move, _ = get_ai_move(board, session["ai_difficulty"])  # MODIFIED: Ignore is_db
    if not suggested_move:
        raise HTTPException(status_code=400, detail="No legal moves available")
    return {
        "suggested_move": suggested_move,
        "session_id": request.session_id,
        "current_turn": current_player_color,
        "is_your_turn": current_player_color == player_color,
        "hint_for": "human player" if current_player_color == player_color else "AI opponent"
    }

@router.get("/game_state/{session_id}", response_model=GameState)
async def get_game_state(session_id: str):
    session = read_game(session_id)
    update_session_activity(session_id)
    board = session["board"]
    game_state = create_game_state(session_id, board, session_data=session)
    game_state.move_history = session["move_history"]
    return game_state

@router.get("/legal_moves/{session_id}")
async def get_legal_moves(session_id: str):
    # Read-only despite the push/pop below: every probe is undone, so the
    # board ends where it started and nothing needs saving.
    session = read_game(session_id)
    update_session_activity(session_id)
    board = session["board"]
    
    # Build enhanced legal moves with check/checkmate info and protection details
    legal_moves_data = []
    for move in board.legal_moves:
        san = board.san(move)
        # Remove +/# from SAN for the move string
        clean_san = san.replace('+', '').replace('#', '')
        
        # Check if this is a capture
        is_capture = board.is_capture(move)
        
        # Check if the target piece is protected (only relevant for captures)
        is_protected = False
        if is_capture:
            target_square = move.to_square
            # Temporarily make the move to check if our piece would be under attack after capturing
            board.push(move)
            # After push(), board.turn has switched to the opponent
            # Check if the opponent (now board.turn) can attack the square we just captured on
            is_protected = board.is_attacked_by(board.turn, target_square)
            board.pop()
        
        # Check if moving to this square puts our piece in danger
        is_vulnerable = False
        if not is_capture:  # Only check vulnerability for non-capture moves
            # Check if the destination square is attacked by opponent
            is_vulnerable = board.is_attacked_by(not board.turn, move.to_square)
        
        # Test the move to see if it gives check or checkmate
        board.push(move)
        gives_check = board.is_check()
        gives_checkmate = board.is_checkmate()
        board.pop()
        
        legal_moves_data.append({
            "move": clean_san,
            "from": chess.square_name(move.from_square),
            "to": chess.square_name(move.to_square),
            "is_capture": is_capture,
            "is_protected": is_protected,
            "is_vulnerable": is_vulnerable,
            "gives_check": gives_check,
            "gives_checkmate": gives_checkmate
        })
    
    # Also provide simple list for backwards compatibility
    simple_moves = [item["move"] for item in legal_moves_data]
    
    return {
        "session_id": session_id,
        "legal_moves": simple_moves,
        "legal_moves_detailed": legal_moves_data,
        "count": len(simple_moves)
    }

@router.delete("/game/{session_id}")
async def delete_game(session_id: str):
    if not game_sessions.delete(session_id):
        raise HTTPException(status_code=404, detail="Game session not found")
    return {"message": f"Game session {session_id} deleted successfully"}

@router.get("/active_games")
async def get_active_games():
    # Now genuinely every active game, not just the ones this worker happens
    # to be holding.
    active_sessions = []
    for session_id, data in game_sessions.items():
        active_sessions.append({
            "session_id": session_id,
            "status": data["status"],
            "player_color": data["player_color"],
            "move_count": len(data["move_history"]),
            "created_at": data["created_at"]
        })
    return {"active_games": active_sessions, "count": len(active_sessions)}

# ============================================
# AUTO-REPLAY ENDPOINTS
# ============================================

@router.get("/games/count")
async def get_games_count():
    """Get total number of games available for replay."""
    return JSONResponse({
        'count': len(parsed_games),
        'loaded': games_loaded
    })

@router.get("/games/players")
async def get_unique_players():
    """Get list of all unique player names from both white and black sides."""
    players = set()
    for game in parsed_games:
        if game['white']:
            players.add(game['white'])
        if game['black']:
            players.add(game['black'])

    # Return sorted list
    return JSONResponse({
        'players': sorted(list(players)),
        'count': len(players)
    })

@router.get("/games/random")
async def get_random_game():
    """Get a random game for auto-replay."""
    if not games_loaded or not parsed_games:
        raise HTTPException(status_code=404, detail="No games loaded")

    game = random.choice(parsed_games)
    return JSONResponse({
        'game_id': game['id'],
        'white': game['white'],
        'black': game['black'],
        'event': game['event'],
        'date': game['date'],
        'result': game['result'],
        'white_elo': game['white_elo'],
        'black_elo': game['black_elo'],
        'move_count': game['move_count'],
        'moves': game['moves']
    })

@router.get("/games/search")
async def search_games(
    player: Optional[str] = None,
    min_moves: Optional[int] = None,
    result: Optional[str] = None
):
    """Search games by criteria."""
    if not games_loaded or not parsed_games:
        raise HTTPException(status_code=404, detail="No games loaded")

    filtered = parsed_games

    if player:
        filtered = [g for g in filtered
                   if player.lower() in g['white'].lower()
                   or player.lower() in g['black'].lower()]

    if min_moves:
        filtered = [g for g in filtered if g['move_count'] >= min_moves]

    if result:
        filtered = [g for g in filtered if g['result'] == result]

    # Return first 50 matches with minimal data
    results = [{
        'game_id': g['id'],
        'white': g['white'],
        'black': g['black'],
        'event': g['event'],
        'date': g['date'],
        'result': g['result'],
        'move_count': g['move_count'],
        'white_elo': g['white_elo'],
        'black_elo': g['black_elo']
    } for g in filtered[:50]]

    return JSONResponse({
        'count': len(filtered),
        'games': results
    })

@router.get("/games/{game_id}")
async def get_game_by_id(game_id: int):
    """Get a specific game by ID."""
    if not games_loaded or not parsed_games:
        raise HTTPException(status_code=404, detail="No games loaded")

    if game_id < 0 or game_id >= len(parsed_games):
        raise HTTPException(status_code=404, detail="Game not found")

    game = parsed_games[game_id]
    return JSONResponse({
        'game_id': game['id'],
        'white': game['white'],
        'black': game['black'],
        'event': game['event'],
        'date': game['date'],
        'result': game['result'],
        'white_elo': game['white_elo'],
        'black_elo': game['black_elo'],
        'move_count': game['move_count'],
        'moves': game['moves']
    })
