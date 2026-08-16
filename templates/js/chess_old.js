// Chess Game Frontend
if (typeof window.ChessGame === 'undefined') {
    window.ChessGame = class ChessGame {
    // Utility: Parse FEN string to board object {square: piece}
    parseFEN(fen) {
        const rows = fen.split(' ')[0].split('/');
        const board = {};
        for (let r = 0; r < 8; r++) {
            let file = 0;
            for (const c of rows[r]) {
                if (c >= '1' && c <= '8') {
                    file += parseInt(c);
                } else {
                    const square = String.fromCharCode(97 + file) + (8 - r);
                    board[square] = c;
                    file++;
                }
            }
        }
        return board;
    }
    constructor() {
        this.sessionId = null;
        this.gameState = null;
        this.selectedSquare = null;
        this.legalMoves = [];
        this.playerColor = 'white';
        this.aiDifficulty = 1;
        this.gameStatus = 'active';
        this.moveHistory = [];
        this.capturedPieces = { white: [], black: [] };
        
        this.initializeBoard();
        this.bindEventListeners();
        this.startNewGame();
    }

    initializeBoard() {
        const board = document.getElementById('chess-board');
        board.innerHTML = '';
        
        for (let rank = 8; rank >= 1; rank--) {
            for (let file = 0; file < 8; file++) {
                const square = document.createElement('div');
                const fileChar = String.fromCharCode(97 + file); // a-h
                const squareId = `${fileChar}${rank}`;
                
                square.className = `square ${(rank + file) % 2 === 0 ? 'dark' : 'light'}`;
                square.dataset.square = squareId;
                // Event handler will be set in updateBoard()
                
                board.appendChild(square);
            }
        }
    }

    bindEventListeners() {
        document.getElementById('new-game-btn').addEventListener('click', () => this.startNewGame());
        document.getElementById('hint-btn').addEventListener('click', () => this.getHint());
        document.getElementById('resign-btn').addEventListener('click', () => this.resign());
        document.getElementById('undo-btn').addEventListener('click', () => this.undoMove());
        
        // Promotion modal
        document.querySelectorAll('.promotion-piece').forEach(btn => {
            btn.addEventListener('click', (e) => this.handlePromotion(e));
        });
    }

    async startNewGame() {
        try {
            this.playerColor = document.getElementById('player-color-select').value;
            this.aiDifficulty = parseInt(document.getElementById('difficulty-select').value);
            
            console.log('Starting new game with:', { player_color: this.playerColor, ai_difficulty: this.aiDifficulty });
            
            const response = await fetch('https://fleminganalytic.com/chess/new_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                mode: 'cors',
                body: JSON.stringify({
                    player_color: this.playerColor,
                    ai_difficulty: this.aiDifficulty
                })
            });
            
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API Error:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            console.log('New game response:', data);
            
            this.sessionId = data.session_id;
            this.gameStatus = 'active';
            this.moveHistory = [];
            this.capturedPieces = { white: [], black: [] };
            
            await this.updateGameState();
            this.updateUI();
            
            this.showMessage('New game started!', 'success');
            
            // If player chose black, apply the suggested move from new_game (if present), then let AI play until it's black's turn
            if (this.playerColor === 'black') {
                // If the backend provides a suggested move in the new_game response, make it
                if (data.suggested_next_move) {
                    await this.makeMove(data.suggested_next_move.substring(0,2), data.suggested_next_move.substring(2,4));
                }
                // Now, if it's still white's turn, let AI play until it's black's turn or game over
                while (this.gameState.current_player === 'white' && this.gameStatus === 'active') {
                    await this.makeAIMove();
                }
            }
            
        } catch (error) {
            console.error('Error starting new game:', error);
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                this.showError('Cannot connect to chess API. Make sure the server is running on https://fleminganalytic.com/chess/');
            } else {
                this.showError(`Failed to start new game: ${error.message}`);
            }
        }
    }

    async updateGameState() {
        try {
            const response = await fetch(`https://fleminganalytic.com/chess/game_state/${this.sessionId}`, {
                method: 'GET',
                mode: 'cors'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }
            
            const data = await response.json();
            console.log('Game state response:', data);
            // Convert FEN to board object if needed
            if (!data.board && data.board_fen) {
                data.board = this.parseFEN(data.board_fen);
            }
            this.gameState = data;
            
            // Get legal moves
            const movesResponse = await fetch(`https://fleminganalytic.com/chess/legal_moves/${this.sessionId}`, {
                method: 'GET',
                mode: 'cors'
            });
            
            if (!movesResponse.ok) {
                throw new Error(`HTTP ${movesResponse.status}: ${await movesResponse.text()}`);
            }
            
            const movesData = await movesResponse.json();
            console.log('Legal moves response:', movesData);
            this.legalMoves = movesData.legal_moves || [];
            
            this.updateBoard();
            this.updateGameInfo();
            this.updateCapturedPieces();
        } catch (error) {
            console.error('Error updating game state:', error);
            this.showError(`Failed to update game state: ${error.message}`);
        }
    }

    updateBoard() {
        if (!this.gameState || !this.gameState.board) {
            console.warn('No board data in gameState:', this.gameState);
            return;
        }
        // Clear all squares
        document.querySelectorAll('.square').forEach(square => {
            square.innerHTML = '';
            square.classList.remove('selected', 'possible-move', 'possible-capture', 'last-move', 'in-check');
            square.removeAttribute('draggable');
            square.ondragstart = null;
            square.ondragover = null;
            square.ondrop = null;
        });

        // Place pieces - using click/tap only (no drag and drop)
        for (const [square, piece] of Object.entries(this.gameState.board)) {
            const squareElement = document.querySelector(`[data-square="${square}"]`);
            if (squareElement) {
                squareElement.innerHTML = piece ? this.getPieceSymbol(piece) : '';
                const pieceSpan = squareElement.querySelector('.piece');
                if (pieceSpan) {
                    // No drag functionality - using click/tap only
                    if (this.gameStatus === 'active' && this.isPieceOwnedByPlayer(piece) && this.gameState.current_player === this.playerColor) {
                        // Enhanced click handler for selecting pieces
                        pieceSpan.onclick = (e) => {
                            e.stopPropagation();
                            this.selectSquare(square);
                        };
                    }
                }
            }
        }

        // Set up click/tap handlers for all squares
        document.querySelectorAll('.square').forEach(squareEl => {
            // Remove any existing onclick to avoid conflicts
            squareEl.onclick = null;
            
            if (this.gameStatus === 'active') {
                // Primary interaction: click/tap to select and move
                squareEl.onclick = async (e) => {
                    const clickedSquare = squareEl.dataset.square;
                    const piece = this.gameState.board[clickedSquare];
                    
                    console.log('Square clicked:', clickedSquare, 'Selected:', this.selectedSquare, 'Piece:', piece);
                    
                    // If we have a piece selected and clicked on a different square
                    if (this.selectedSquare && this.selectedSquare !== clickedSquare) {
                        const isLegal = this.isLegalMove(this.selectedSquare, clickedSquare);
                        console.log('Attempting move from', this.selectedSquare, 'to', clickedSquare, 'Legal:', isLegal);
                        
                        if (isLegal) {
                            await this.makeMove(this.selectedSquare, clickedSquare);
                            this.clearSelection();
                        } else {
                            // Clicked on invalid square - clear selection
                            this.clearSelection();
                            // If clicked on own piece, select it instead
                            if (piece && this.isPieceOwnedByPlayer(piece) && this.gameState.current_player === this.playerColor) {
                                this.selectSquare(clickedSquare);
                            }
                        }
                    } 
                    // If clicking on the already selected square, deselect it
                    else if (this.selectedSquare === clickedSquare) {
                        this.clearSelection();
                    }
                    // If no piece selected and clicking on own piece, select it
                    else if (piece && this.isPieceOwnedByPlayer(piece) && this.gameState.current_player === this.playerColor) {
                        this.selectSquare(clickedSquare);
                    }
                };
            }
        });

        // Highlight last move
        if (this.gameState.last_move) {
            const { from: fromSquare, to: toSquare } = this.gameState.last_move;
            const fromElement = document.querySelector(`[data-square="${fromSquare}"]`);
            const toElement = document.querySelector(`[data-square="${toSquare}"]`);
            if (fromElement) fromElement.classList.add('last-move');
            if (toElement) toElement.classList.add('last-move');
        }

        // Highlight king in check
        if (this.gameState.in_check) {
            const kingSquare = this.findKing(this.gameState.current_player);
            if (kingSquare) {
                const kingElement = document.querySelector(`[data-square="${kingSquare}"]`);
                if (kingElement) kingElement.classList.add('in-check');
            }
        }
    }

    getPieceSymbol(piece) {
        const symbols = {
            'P': '♙', 'p': '♟',
            'R': '♖', 'r': '♜',
            'N': '♘', 'n': '♞',
            'B': '♗', 'b': '♝',
            'Q': '♕', 'q': '♛',
            'K': '♔', 'k': '♚'
        };
        return `<span class="piece">${symbols[piece] || piece}</span>`;
    }

    findKing(color) {
        const kingSymbol = color === 'white' ? 'K' : 'k';
        for (const [square, piece] of Object.entries(this.gameState.board)) {
            if (piece === kingSymbol) {
                return square;
            }
        }
        return null;
    }

    async handleSquareClick(event) {
        if (this.gameStatus !== 'active') return;
        if (this.gameState && this.gameState.current_player !== this.playerColor) return;
        
        const square = event.currentTarget.dataset.square;
        const piece = this.gameState.board[square];
        
        if (this.selectedSquare === square) {
            // Deselect
            this.clearSelection();
        } else if (this.selectedSquare && this.isLegalMove(this.selectedSquare, square)) {
            // Make move
            await this.makeMove(this.selectedSquare, square);
        } else if (piece && this.isPieceOwnedByPlayer(piece)) {
            // Select new piece
            this.selectSquare(square);
        } else {
            // Clear selection if clicking on empty square or opponent piece
            this.clearSelection();
        }
    }

    isPieceOwnedByPlayer(piece) {
        if (this.playerColor === 'white') {
            return piece === piece.toUpperCase(); // White pieces are uppercase
        } else {
            return piece === piece.toLowerCase(); // Black pieces are lowercase
        }
    }

    selectSquare(square) {
        this.clearSelection();
        this.selectedSquare = square;
        
        const squareElement = document.querySelector(`[data-square="${square}"]`);
        squareElement.classList.add('selected');
        
        // Get valid move targets for this square
        const validTargets = this.getPossibleMovesForSquare(square);
        
        // Highlight possible moves
        validTargets.forEach(targetSquare => {
            const targetElement = document.querySelector(`[data-square="${targetSquare}"]`);
            if (targetElement) {
                if (this.gameState.board[targetSquare]) {
                    targetElement.classList.add('possible-capture');
                } else {
                    targetElement.classList.add('possible-move');
                }
            }
        });
    }

    getPossibleMovesForSquare(from) {
        // Filter legal moves by the from square
        return this.legalMoves.filter(m => m.from === from).map(m => m.to);
    }

    clearSelection() {
        this.selectedSquare = null;
        document.querySelectorAll('.square').forEach(square => {
            square.classList.remove('selected', 'possible-move', 'possible-capture');
        });
    }

    isLegalMove(from, to) {
        // Check if there's a legal move from 'from' to 'to'
        return this.legalMoves.some(m => m.from === from && m.to === to);
    }

    async makeMove(from, to) {
        try {
            let move = from + to;
            // Only show promotion modal if a pawn is moving to the last rank
            const piece = this.gameState.board[from];
            const isPromotion = (piece === 'P' && to[1] === '8') || (piece === 'p' && to[1] === '1');
            if (isPromotion) {
                const promotionPiece = await this.showPromotionModal();
                move += promotionPiece;
            }
            console.log('Sending move to backend:', move);
            const response = await fetch('https://fleminganalytic.com/chess/make_move', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                mode: 'cors',
                body: JSON.stringify({
                    session_id: this.sessionId,
                    move: move
                })
            });
            const data = await response.json();
            console.log('Backend move response:', data);
            if (response.ok) {
                await this.updateGameState();
                this.clearSelection();
                // Check for game end
                if (data.game_over) {
                    this.gameStatus = 'finished';
                    this.showGameResult(data);
                } else if (this.gameState.current_player !== this.playerColor) {
                    // AI's turn
                    setTimeout(() => this.makeAIMove(), 500);
                }
            } else {
                this.showError(data.error || 'Invalid move');
            }
        } catch (error) {
            console.error('Error making move:', error);
            this.showError('Failed to make move: ' + error.message);
        }
    }

    async makeAIMove() {
        try {
            // Show a visible 'thinking' message
            const gameStatusElement = document.getElementById('game-status');
            const oldText = gameStatusElement.textContent;
            gameStatusElement.textContent = 'AI is thinking...';
            gameStatusElement.classList.remove('check-warning', 'game-over');
            // Wait 1 second
            await new Promise(resolve => setTimeout(resolve, 1000));
            const response = await fetch('https://fleminganalytic.com/chess/get_ai_move', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                mode: 'cors',
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
            const data = await response.json();
            // Restore status text
            gameStatusElement.textContent = oldText;
            if (response.ok) {
                await this.updateGameState();
                if (data.game_over) {
                    this.gameStatus = 'finished';
                    this.showGameResult(data);
                }
            } else {
                console.error('AI move error:', data.error);
            }
        } catch (error) {
            console.error('Error getting AI move:', error);
        }
    }

    async getHint() {
        // Use the latest gameState for hint and explanation
        if (this.gameState && this.gameState.suggested_next_move) {
            this.showHintDialog(this.gameState.suggested_next_move, this.gameState.move_explanation);
        } else {
            this.showError('No hint available');
        }
    }

    showHintDialog(hint, explanation) {
        // Remove any existing dialog
        let oldDialog = document.getElementById('hint-dialog');
        if (oldDialog) oldDialog.remove();

        const from = hint.substring(0, 2);
        const to = hint.substring(2, 4);

        const dialog = document.createElement('div');
        dialog.id = 'hint-dialog';
        dialog.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #fff;
            border: 2px solid #3498db;
            border-radius: 10px;
            box-shadow: 0 4px 32px rgba(0,0,0,0.25);
            padding: 32px 28px 20px 28px;
            z-index: 2000;
            min-width: 320px;
            text-align: center;
        `;
        dialog.innerHTML = `
            <div style="font-size: 1.2em; margin-bottom: 10px; color: #222; font-weight: bold;">Suggested Move</div>
            <div style="font-size: 1.5em; margin-bottom: 10px; color: #3498db;">${from} → ${to}</div>
            <div style="margin-bottom: 18px; color: #444;">${explanation ? explanation : ''}</div>
            <button id="make-hint-move" style="margin-right: 12px; padding: 8px 18px; font-size: 1em; background: #27ae60; color: #fff; border: none; border-radius: 5px; cursor: pointer;">Make this move</button>
            <button id="close-hint-dialog" style="padding: 8px 18px; font-size: 1em; background: #bbb; color: #fff; border: none; border-radius: 5px; cursor: pointer;">Close</button>
        `;
        document.body.appendChild(dialog);

        document.getElementById('close-hint-dialog').onclick = () => dialog.remove();
        document.getElementById('make-hint-move').onclick = async () => {
            dialog.remove();
            await this.makeMove(from, to);
        };
    }

    showPromotionModal() {
        return new Promise((resolve) => {
            const modal = document.getElementById('promotion-modal');
            modal.classList.remove('hidden');
            
            const handlePromotion = (event) => {
                const piece = event.target.dataset.piece;
                modal.classList.add('hidden');
                document.querySelectorAll('.promotion-piece').forEach(btn => {
                    btn.removeEventListener('click', handlePromotion);
                });
                resolve(piece);
            };
            
            document.querySelectorAll('.promotion-piece').forEach(btn => {
                btn.addEventListener('click', handlePromotion);
            });
        });
    }

    updateGameInfo() {
        if (!this.gameState) return;
        const currentPlayerElement = document.getElementById('current-player');
        const gameStatusElement = document.getElementById('game-status');
        if (this.gameStatus === 'active') {
            const currentPlayer = this.gameState.current_player;
            currentPlayerElement.textContent = `${currentPlayer.charAt(0).toUpperCase() + currentPlayer.slice(1)} to move`;
            if (this.gameState.in_check) {
                gameStatusElement.textContent = 'Check!';
                gameStatusElement.classList.add('check-warning');
            } else {
                gameStatusElement.textContent = '';
                gameStatusElement.classList.remove('check-warning');
            }
        }
        this.updateMoveHistory();
        // this.updateCapturedPieces(); // Now called in updateGameState
    }

    updateCapturedPieces() {
        // Calculate captured pieces by comparing initial set to current board
        const initial = {
            white: ['P','P','P','P','P','P','P','P','R','R','N','N','B','B','Q','K'],
            black: ['p','p','p','p','p','p','p','p','r','r','n','n','b','b','q','k']
        };
        const current = { white: [], black: [] };
        for (const piece of Object.values(this.gameState.board)) {
            if ('PRNBQK'.includes(piece)) current.white.push(piece);
            if ('prnbqk'.includes(piece)) current.black.push(piece);
        }
        function diff(start, now) {
            const copy = now.slice();
            return start.filter(x => {
                const idx = copy.indexOf(x);
                if (idx !== -1) { copy.splice(idx,1); return false; }
                return true;
            });
        }
        const capturedWhite = diff(initial.black, current.black);
        const capturedBlack = diff(initial.white, current.white);
        // Render captured pieces
        const wDiv = document.getElementById('captured-white-pieces');
        const bDiv = document.getElementById('captured-black-pieces');
        wDiv.innerHTML = capturedWhite.map(p => this.getPieceSymbol(p)).join(' ');
        bDiv.innerHTML = capturedBlack.map(p => this.getPieceSymbol(p)).join(' ');
    }

    updateMoveHistory() {
        const movesList = document.getElementById('moves-list');
        if (!this.gameState.move_history) return;
        movesList.innerHTML = '';
        const moves = this.gameState.move_history;
        // Try to use move_details if present, else fallback to parsing
        let details = this.gameState.move_details;
        if (!details) {
            // Fallback: try to infer from move_history and board state
            details = this.inferMoveDetails(moves);
        }
        for (let i = 0; i < moves.length; i += 2) {
            const moveNumber = Math.floor(i / 2) + 1;
            const whiteDetail = details[i];
            const blackDetail = details[i + 1];
            const movePair = document.createElement('div');
            movePair.className = 'move-pair';
            // Move number
            const moveNumberElement = document.createElement('span');
            moveNumberElement.className = 'move-number';
            moveNumberElement.textContent = `${moveNumber}.`;
            movePair.appendChild(moveNumberElement);
            // White move
            const whiteMoveElement = document.createElement('span');
            whiteMoveElement.className = 'move move-white';
            whiteMoveElement.innerHTML = this.formatMoveDetail(whiteDetail);
            movePair.appendChild(whiteMoveElement);
            // Black move
            const blackMoveElement = document.createElement('span');
            blackMoveElement.className = 'move move-black';
            blackMoveElement.innerHTML = this.formatMoveDetail(blackDetail);
            movePair.appendChild(blackMoveElement);
            movesList.appendChild(movePair);
        }
        // Scroll to bottom
        movesList.scrollTop = movesList.scrollHeight;
    }

    inferMoveDetails(moves) {
        // Fallback: just show algebraic notation with a generic piece symbol
        return moves.map(m => {
            if (!m) return null;
            // Guess piece type from notation
            let piece = 'P';
            let from = '';
            let to = '';
            let capture = false;
            // If starts with uppercase letter, it's a piece
            if (/^[KQRBN]/.test(m)) piece = m[0];
            // If contains 'x', it's a capture
            if (m.includes('x')) capture = true;
            // Try to extract destination square (last 2 chars)
            const match = m.match(/([a-h][1-8])$/);
            if (match) to = match[1];
            // For from, just show '' (not available)
            return { piece, from, to, capture };
        });
    }

    formatMoveDetail(detail) {
    if (!detail) return '';
    // detail: {piece, from, to, capture}
    const letter = detail.piece ? detail.piece.toUpperCase() : '';
    const arrow = detail.capture ? '×' : '→';
    // Always show letter, e.g. P e2→e4
    return `${letter} ${detail.from} ${arrow} ${detail.to}`;
    }

    updateUI() {
        const undoBtn = document.getElementById('undo-btn');
        undoBtn.disabled = this.gameStatus !== 'active' || !this.gameState || this.gameState.move_history.length === 0;
    }

    showGameResult(data) {
        const gameStatusElement = document.getElementById('game-status');
        gameStatusElement.classList.remove('check-warning');
        gameStatusElement.classList.remove('game-over');
        let msg = '';
        if (data.checkmate) {
            const winner = this.gameState.current_player === 'white' ? 'Black' : 'White';
            msg = `Checkmate! ${winner} wins!`;
            gameStatusElement.classList.add('game-over');
        } else if (data.stalemate) {
            msg = 'Stalemate! Draw!';
            gameStatusElement.classList.add('game-over');
        } else if (data.draw) {
            msg = 'Draw!';
            gameStatusElement.classList.add('game-over');
        }
        gameStatusElement.textContent = msg;
        this.showMessage(msg, 'success');
    }

    showMessage(message, type = 'info') {
        // Create a temporary message element
        const messageEl = document.createElement('div');
        messageEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
        
        const colors = {
            info: '#3498db',
            success: '#27ae60',
            error: '#e74c3c'
        };
        
        messageEl.style.backgroundColor = colors[type] || colors.info;
        messageEl.textContent = message;
        
        document.body.appendChild(messageEl);
        
        setTimeout(() => {
            messageEl.remove();
        }, 3000);
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    async resign() {
        if (confirm('Are you sure you want to resign?')) {
            this.gameStatus = 'finished';
            const gameStatusElement = document.getElementById('game-status');
            gameStatusElement.textContent = 'Game resigned';
            this.showMessage('You resigned the game', 'info');
        }
    }

    async undoMove() {
        // This would require an undo endpoint in the API
        this.showMessage('Undo not implemented yet', 'info');
    }
} // <-- End of ChessGame class

    // export assignment already done via window.ChessGame
} // end guard for template ChessGame

// Add CSS animation for messages
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChessGame();
});
