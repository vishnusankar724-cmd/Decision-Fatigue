import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import chess
import chess.pgn
import io

df = pd.read_csv('C:\\Users\\vishn\\Desktop\\p2.decision_fatigue\\archive (1)\\club_games_data.csv')
df = df.head(400)
df.head()

def parse_game(pgn_string):
    try:
        game = chess.pgn.read_game(io.StringIO(pgn_string))
        moves = []
        board = game.board()
        
        for move in game.mainline_moves():
            board.push(move)
            moves.append(move.uci())
        
        return moves
    except:
        return []

def calculate_move_complexity(fen):
    board = chess.Board(fen)
    return len(list(board.legal_moves))

df['moves'] = df['pgn'].apply(parse_game)
df['total_moves'] = df['moves'].apply(len)
df = df[df['total_moves'] > 10]

all_move_data = []

for idx, row in df.iterrows():
    game = chess.pgn.read_game(io.StringIO(row['pgn']))
    board = game.board()
    move_num = 1
    
    for move in game.mainline_moves():
        legal_moves = len(list(board.legal_moves))
        board.push(move)
        
        all_move_data.append({
            'game_id': idx,
            'move_number': move_num,
            'complexity': legal_moves,
            #'result': row['result']
        })
        move_num += 1

move_df = pd.DataFrame(all_move_data)

move_df['error_proxy'] = move_df['complexity'] / move_df.groupby('game_id')['complexity'].transform('mean')
move_df['move_phase'] = pd.cut(move_df['move_number'], 
                                bins=[0, 15, 30, 50, 100], 
                                labels=['Opening', 'Midgame', 'Late', 'Endgame'])

phase_errors = move_df.groupby('move_phase')['error_proxy'].agg(['mean', 'std', 'count'])

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
move_df.groupby('move_number')['error_proxy'].mean().rolling(5).mean().plot()
plt.xlabel('Move Number')
plt.ylabel('Decision Difficulty')
plt.title('Decision Fatigue Over Game Progression')

plt.subplot(1, 2, 2)
phase_errors['mean'].plot(kind='bar', yerr=phase_errors['std'])
plt.xlabel('Game Phase')
plt.ylabel('Average Decision Difficulty')
plt.title('Fatigue by Game Phase')
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()

bins = list(range(0, int(move_df['move_number'].max()) + 5, 5))
move_df['move_bin'] = pd.cut(move_df['move_number'], bins=bins)

binned_stats = move_df.groupby('move_bin')['error_proxy'].agg(['mean', 'count'])
binned_stats = binned_stats[binned_stats['count'] > 30]

plt.figure(figsize=(10, 6))
plt.plot(range(len(binned_stats)), binned_stats['mean'], marker='o')
plt.xlabel('Game Progression (5-move bins)')
plt.ylabel('Decision Difficulty Score')
plt.title('Does Decision Quality Degrade Over Time?')
plt.grid(True, alpha=0.3)
plt.show()

early_game = move_df[move_df['move_number'] <= 15]['error_proxy'].mean()
late_game = move_df[move_df['move_number'] >= 40]['error_proxy'].mean()
degradation = ((late_game - early_game) / early_game) * 100

results = pd.DataFrame({
    'Phase': ['Early Game (1-15)', 'Late Game (40+)', 'Degradation %'],
    'Score': [early_game, late_game, degradation]
})

#results

early_game = move_df[move_df['move_number'] <= 15]['error_proxy'].mean()
late_game = move_df[move_df['move_number'] >= 40]['error_proxy'].mean()
degradation = ((late_game - early_game) / early_game) * 100

print(f"Early Game Score: {early_game:.2f}")
print(f"Late Game Score: {late_game:.2f}")
print(f"Degradation: {degradation:.2f}%")