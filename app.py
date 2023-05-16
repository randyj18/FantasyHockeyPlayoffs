import cmath
import sqlite3
from flask import Flask, render_template
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'

def get_goals(player_id):
    player_stats_url = f'https://statsapi.web.nhl.com/api/v1/people/{player_id}/stats?stats=statsSingleSeasonPlayoffs&season=20222023'
    response = requests.get(player_stats_url)
    try:
        data = response.json()
        goals = data['stats'][0]['splits'][0]['stat']['goals']
    except (IndexError, KeyError):
        goals = 0
    return goals


def get_assists(player_id):
    url = f"https://statsapi.web.nhl.com/api/v1/people/{player_id}/stats?stats=statsSingleSeasonPlayoffs&season=20222023"
    response = requests.get(url)
    data = response.json()

    try:
        assists = data['stats'][0]['splits'][0]['stat']['assists']
    except (IndexError, KeyError):
        assists = 0

    return assists

def get_wins(player_id):
    player_stats_url = f'https://statsapi.web.nhl.com/api/v1/people/{player_id}/stats?stats=statsSingleSeasonPlayoffs&season=20222023'
    response = requests.get(player_stats_url)
    try:
        data = response.json()
        wins = data['stats'][0]['splits'][0]['stat']['wins']
    except (IndexError, KeyError):
        wins = 0
    return wins

def get_shutouts(player_id):
    player_stats_url = f'https://statsapi.web.nhl.com/api/v1/people/{player_id}/stats?stats=statsSingleSeasonPlayoffs&season=20222023'
    response = requests.get(player_stats_url)
    try:
        data = response.json()
        shutouts = data['stats'][0]['splits'][0]['stat']['shutouts']
    except (IndexError, KeyError):
        shutouts = 0
    return shutouts

@app.route('/')
def index():
    conn = sqlite3.connect('player_stats.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS Player_Stats')
    c.execute('''CREATE TABLE IF NOT EXISTS Player_Stats
                (Manager text, Player text, Player_ID integer, Goals integer,
                Assists integer, Points integer, Gordie_Howe_Hattricks integer,
                Conn_Smythe integer, Pts_Before_Acquiring integer, Total_Points integer)''')
    url = 'https://raw.githubusercontent.com/randyj18/FantasyPlayoffPool/main/TeamInfo.json'
    response = requests.get(url)
    data = response.json()

    # Create a dictionary to store the running totals for each manager
    manager_totals = {}

    for player_info in data:
        manager = player_info['Team']
        player = player_info['Player']
        player_id = player_info['Player ID']
        goals = get_goals(player_id)
        assists = get_assists(player_id)
        points = goals + assists
        gordie_howe_hattricks = int(player_info['Points for Gordie Howe Hattricks'])
        conn_smythe = int(player_info['Points for Conn Smythe'])
        pts_before_acquiring = int(player_info['Points Before Acquiring'])
        total_points = points + gordie_howe_hattricks + conn_smythe - pts_before_acquiring

        # Update the running total for the manager
        manager_totals[manager] = manager_totals.get(manager, 0) + total_points

        c.execute("INSERT INTO Player_Stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (manager, player, player_id, goals, assists, points, gordie_howe_hattricks, conn_smythe, pts_before_acquiring, total_points))

    conn.commit()
    c.execute("SELECT * FROM Player_Stats")
    rows = c.fetchall()
    player_stats = []
    for row in rows:
        player_stats.append({
            'Manager': row[0],
            'Player': row[1],
            'Player ID': row[2],
            'Goals': row[3],
            'Assists': row[4],
            'Points': row[5],
            'Gordie Howe Hattricks': row[6],
            'Conn Smythe': row[7],
            'Pts Before Acquiring': row[8],
            'Total Points': row[9]
        })
    conn.close()

    conn = sqlite3.connect('goalie_stats.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS Goalie_Stats')
    c.execute('''CREATE TABLE IF NOT EXISTS Goalie_Stats
                (gManager text, gPlayer text, gPlayer_ID integer, Wins integer,
                Shutouts integer, gAssists integer, gPts_Before_Acquiring integer, gTotal_Points integer)''')
    url = 'https://raw.githubusercontent.com/randyj18/FantasyPlayoffPool/main/GoalieInfo.json'
    response = requests.get(url)
    data = response.json()
    for goalie_info in data:
        gmanager = goalie_info['Team']
        gplayer = goalie_info['Player']
        gplayer_id = goalie_info['Player ID']
        wins = get_wins(gplayer_id)
        shutouts = get_shutouts(gplayer_id)
        gassists = int(goalie_info['Assists'])
        gpts_before_acquiring = int(goalie_info['Points Before Acquiring'])
        gtotal_points = (wins * 2) + shutouts + gassists - gpts_before_acquiring

        # Update the running total for the manager
        manager_totals[gmanager] = manager_totals.get(gmanager, 0) + gtotal_points

        c.execute("INSERT INTO Goalie_Stats VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (gmanager, gplayer, gplayer_id, wins, shutouts, gassists, gpts_before_acquiring, gtotal_points))

    conn.commit()
    c.execute("SELECT * FROM Goalie_Stats")
    rows = c.fetchall()
    goalie_stats = []
    for row in rows:
        goalie_stats.append({
            'Manager': row[0],
            'Player': row[1],
            'Player ID': row[2],
            'Wins': row[3],
            'Shutouts': row[4],
            'Assists': row[5],
            'Points Before Acquiring': row[6],
            'Total Points': row[7]
        })
    conn.close()

    sorted_manager_totals = dict(sorted(manager_totals.items(), key=lambda x: x[1], reverse=True))

    return render_template('index.html', player_stats=player_stats, goalie_stats=goalie_stats, manager_totals=sorted_manager_totals)

if __name__ == '__main__':
    app.run(debug=True)

