import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import numpy as np
from datetime import datetime
import re

# Database connection parameters
DB_PARAMS = {
    'dbname': 'ipl_2008_2024',
    'user': 'skye',
    'host': 'localhost',
    'password': 'skye'  # Add your password if needed
}

def connect_to_db():
    """Create a connection to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

def load_data():
    """Load data from CSV files"""
    try:
        matches_df = pd.read_csv('F:/Skye_analytics_2.0/backend/data/matches.csv')
        deliveries_df = pd.read_csv('F:/Skye_analytics_2.0/backend/data/deliveries.csv')
        return matches_df, deliveries_df
    except Exception as e:
        print(f"Error loading CSV files: {e}")
        return None, None

def extract_unique_data(matches_df, deliveries_df):
    """Extract unique data for teams, venues, seasons, and players"""
    
    # Extract unique teams
    teams = set()
    teams.update(matches_df['team1'].unique())
    teams.update(matches_df['team2'].unique())
    teams = sorted([team for team in teams if pd.notna(team)])
    
    # Create team short names (e.g., Royal Challengers Bangalore -> RCB)
    team_short_names = {}
    for team in teams:
        # Extract initials from team name
        initials = ''.join([word[0] for word in team.split() if word[0].isupper()])
        team_short_names[team] = initials if initials else team[:3].upper()
    
    # Extract unique venues
    venues = sorted([venue for venue in matches_df['venue'].unique() if pd.notna(venue)])
    
    # Extract cities from venues
    venue_city_map = {}
    for venue, city in zip(matches_df['venue'], matches_df['city']):
        if pd.notna(venue) and pd.notna(city):
            venue_city_map[venue] = city
    
    # Extract unique seasons and map to proper format
    seasons = sorted([season for season in matches_df['season'].unique() if pd.notna(season)])
    season_year_map = {}
    for season in seasons:
        if '/' in str(season):  # Format like "2007/08"
            year = int(str(season).split('/')[0])
        else:  # Format like 2016
            year = int(season)
        season_year_map[season] = year
    
    # Extract unique players
    players = set()
    # From matches (player of match)
    players.update([player for player in matches_df['player_of_match'].unique() if pd.notna(player)])
    
    # From deliveries
    players.update([player for player in deliveries_df['batter'].unique() if pd.notna(player)])
    players.update([player for player in deliveries_df['bowler'].unique() if pd.notna(player)])
    players.update([player for player in deliveries_df['non_striker'].unique() if pd.notna(player)])
    
    # Add dismissed players and fielders
    players.update([player for player in deliveries_df['player_dismissed'].unique() 
                   if pd.notna(player) and player != 'NA'])
    players.update([player for player in deliveries_df['fielder'].unique() 
                   if pd.notna(player) and player != 'NA'])
    
    players = sorted(list(players))
    
    return teams, team_short_names, venues, venue_city_map, seasons, season_year_map, players

def insert_teams(conn, teams, team_short_names):
    """Insert teams into the database"""
    try:
        cursor = conn.cursor()
        team_data = [(team, team_short_names.get(team, team[:3].upper()), None) for team in teams]
        
        query = """
        INSERT INTO teams (team_name, team_short_name, home_venue)
        VALUES (%s, %s, %s)
        ON CONFLICT (team_name) DO UPDATE 
        SET team_short_name = EXCLUDED.team_short_name
        RETURNING team_id, team_name;
        """
        
        # Execute batch insert
        execute_batch(cursor, query, team_data)
        
        # Fetch the inserted teams with their IDs
        cursor.execute("SELECT team_id, team_name FROM teams;")
        team_id_map = {name: id for id, name in cursor.fetchall()}
        
        conn.commit()
        cursor.close()
        print(f"Successfully inserted {len(teams)} teams.")
        return team_id_map
    
    except Exception as e:
        conn.rollback()
        print(f"Error inserting teams: {e}")
        return {}

def insert_venues(conn, venues, venue_city_map):
    """Insert venues into the database"""
    try:
        cursor = conn.cursor()
        venue_data = [(venue, venue_city_map.get(venue, None)) for venue in venues]
        
        query = """
        INSERT INTO venues (venue_name, city)
        VALUES (%s, %s)
        ON CONFLICT (venue_name) DO UPDATE 
        SET city = CASE WHEN EXCLUDED.city IS NOT NULL THEN EXCLUDED.city ELSE venues.city END
        RETURNING venue_id, venue_name;
        """
        
        # Execute batch insert
        execute_batch(cursor, query, venue_data)
        
        # Fetch the inserted venues with their IDs
        cursor.execute("SELECT venue_id, venue_name FROM venues;")
        venue_id_map = {name: id for id, name in cursor.fetchall()}
        
        conn.commit()
        cursor.close()
        print(f"Successfully inserted {len(venues)} venues.")
        return venue_id_map
    
    except Exception as e:
        conn.rollback()
        print(f"Error inserting venues: {e}")
        return {}

def insert_players(conn, players):
    """Insert players into the database"""
    try:
        cursor = conn.cursor()
        player_data = [(player, None, None, None, None) for player in players]
        
        query = """
        INSERT INTO players (player_name, country, playing_role, batting_style, bowling_style)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        RETURNING player_id, player_name;
        """
        
        # Execute batch insert
        execute_batch(cursor, query, player_data, page_size=1000)
        
        # Fetch the inserted players with their IDs
        cursor.execute("SELECT player_id, player_name FROM players;")
        player_id_map = {name: id for id, name in cursor.fetchall()}
        
        conn.commit()
        cursor.close()
        print(f"Successfully inserted {len(players)} players.")
        return player_id_map
    
    except Exception as e:
        conn.rollback()
        print(f"Error inserting players: {e}")
        return {}

def insert_seasons(conn, seasons, season_year_map):
    """Insert seasons into the database"""
    try:
        cursor = conn.cursor()
        season_data = []
        
        for season in seasons:
            year = season_year_map.get(season, None)
            if year:
                # Estimate start/end dates based on the IPL typical schedule
                if '/' in str(season):  # Format like "2007/08"
                    season_data.append((str(season), year, f"{year}-04-01", f"{year}-06-01"))
                else:  # Format like 2016
                    season_data.append((str(season), year, f"{year}-04-01", f"{year}-06-01"))
        
        query = """
        INSERT INTO seasons (season_name, season_year, start_date, end_date)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (season_name) DO UPDATE 
        SET season_year = EXCLUDED.season_year
        RETURNING season_id, season_name;
        """
        
        # Execute batch insert
        execute_batch(cursor, query, season_data)
        
        # Fetch the inserted seasons with their IDs
        cursor.execute("SELECT season_id, season_name FROM seasons;")
        season_id_map = {str(name): id for id, name in cursor.fetchall()}
        
        conn.commit()
        cursor.close()
        print(f"Successfully inserted {len(seasons)} seasons.")
        return season_id_map
    
    except Exception as e:
        conn.rollback()
        print(f"Error inserting seasons: {e}")
        return {}

def parse_date(date_str):
    """Parse date from string to ISO format"""
    try:
        if pd.isna(date_str):
            return None
        
        # Try different date formats
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
            try:
                date_obj = datetime.strptime(str(date_str), fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    except Exception:
        return None

def insert_matches(conn, matches_df, team_id_map, venue_id_map, season_id_map, player_id_map):
    """Insert matches into the database"""
    try:
        cursor = conn.cursor()
        match_data = []
        
        for _, row in matches_df.iterrows():
            # Convert values safely
            match_id = int(row['id']) if pd.notna(row['id']) else None
            season_id = season_id_map.get(str(row['season']), None) if pd.notna(row['season']) else None
            match_date = parse_date(row['date'])
            venue_id = venue_id_map.get(row['venue'], None) if pd.notna(row['venue']) else None
            team1_id = team_id_map.get(row['team1'], None) if pd.notna(row['team1']) else None
            team2_id = team_id_map.get(row['team2'], None) if pd.notna(row['team2']) else None
            toss_winner_id = team_id_map.get(row['toss_winner'], None) if pd.notna(row['toss_winner']) else None
            toss_decision = row['toss_decision'].lower() if pd.notna(row['toss_decision']) else None
            winner_id = team_id_map.get(row['winner'], None) if pd.notna(row['winner']) else None
            result = row['result'] if pd.notna(row['result']) else None
            result_margin = float(row['result_margin']) if pd.notna(row['result_margin']) else None
            player_of_match_id = player_id_map.get(row['player_of_match'], None) if pd.notna(row['player_of_match']) else None
            match_type = row['match_type'] if pd.notna(row['match_type']) else None
            target_runs = float(row['target_runs']) if pd.notna(row['target_runs']) else None
            target_overs = float(row['target_overs']) if pd.notna(row['target_overs']) else None
            is_super_over = True if pd.notna(row['super_over']) and row['super_over'] == 'Y' else False
            dl_method = row['method'] if pd.notna(row['method']) and row['method'] != 'NA' else None
            umpire1 = row['umpire1'] if pd.notna(row['umpire1']) else None
            umpire2 = row['umpire2'] if pd.notna(row['umpire2']) else None
            
            match_data.append((
                match_id, season_id, match_date, venue_id, team1_id, team2_id, 
                toss_winner_id, toss_decision, winner_id, result, result_margin, 
                player_of_match_id, match_type, target_runs, target_overs, 
                is_super_over, dl_method, umpire1, umpire2
            ))
        
        query = """
        INSERT INTO matches (
            match_id, season_id, match_date, venue_id, team1_id, team2_id, 
            toss_winner_id, toss_decision, winner_id, result, result_margin, 
            player_of_match_id, match_type, target_runs, target_overs, 
            is_super_over, dl_method, umpire1, umpire2
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (match_id) DO UPDATE 
        SET 
            season_id = EXCLUDED.season_id,
            match_date = EXCLUDED.match_date,
            venue_id = EXCLUDED.venue_id,
            team1_id = EXCLUDED.team1_id,
            team2_id = EXCLUDED.team2_id,
            toss_winner_id = EXCLUDED.toss_winner_id,
            toss_decision = EXCLUDED.toss_decision,
            winner_id = EXCLUDED.winner_id,
            result = EXCLUDED.result,
            result_margin = EXCLUDED.result_margin,
            player_of_match_id = EXCLUDED.player_of_match_id,
            match_type = EXCLUDED.match_type,
            target_runs = EXCLUDED.target_runs,
            target_overs = EXCLUDED.target_overs,
            is_super_over = EXCLUDED.is_super_over,
            dl_method = EXCLUDED.dl_method,
            umpire1 = EXCLUDED.umpire1,
            umpire2 = EXCLUDED.umpire2;
        """
        
        # Execute batch insert
        execute_batch(cursor, query, match_data, page_size=100)
        
        conn.commit()
        cursor.close()
        print(f"Successfully inserted {len(match_data)} matches.")
    
    except Exception as e:
        conn.rollback()
        print(f"Error inserting matches: {e}")
def insert_innings(conn, deliveries_df, team_id_map):
    """Create and insert innings data from deliveries with improved error handling"""
    try:
        cursor = conn.cursor()
        
        # Get unique innings from deliveries
        innings_data = deliveries_df.groupby(['match_id', 'inning', 'batting_team', 'bowling_team']).size().reset_index(name='count')
        
        # First, ensure we have innings records for all matches in the database
        cursor.execute("""
        SELECT m.match_id, m.team1_id, m.team2_id 
        FROM matches m
        LEFT JOIN innings i ON m.match_id = i.match_id
        WHERE i.inning_id IS NULL
        """)
        
        missing_match_innings = cursor.fetchall()
        
        # If we found matches without innings, create default innings for them
        if missing_match_innings:
            print(f"Found {len(missing_match_innings)} matches without innings records. Creating default innings...")
            default_innings = []
            
            for match_id, team1_id, team2_id in missing_match_innings:
                # Create default innings 1 (team1 batting, team2 bowling)
                default_innings.append((match_id, 1, team1_id, team2_id))
                # Create default innings 2 (team2 batting, team1 bowling)
                default_innings.append((match_id, 2, team2_id, team1_id))
                
            # Insert default innings
            default_query = """
            INSERT INTO innings (match_id, inning_number, batting_team_id, bowling_team_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (match_id, inning_number) DO UPDATE 
            SET 
                batting_team_id = EXCLUDED.batting_team_id,
                bowling_team_id = EXCLUDED.bowling_team_id
            """
            
            execute_batch(cursor, default_query, default_innings, page_size=100)
            
            print(f"Created {len(default_innings)} default innings records.")
        
        # Now proceed with innings from deliveries data for more accurate team assignments
        inning_records = []
        for _, row in innings_data.iterrows():
            match_id = int(row['match_id']) if pd.notna(row['match_id']) else None
            inning_number = int(row['inning']) if pd.notna(row['inning']) else None
            batting_team_id = team_id_map.get(row['batting_team'], None) if pd.notna(row['batting_team']) else None
            bowling_team_id = team_id_map.get(row['bowling_team'], None) if pd.notna(row['bowling_team']) else None
            
            # Skip if we're missing critical information
            if match_id is None or inning_number is None:
                print(f"Warning: Skipping innings record due to missing data - match_id: {match_id}, inning: {inning_number}")
                continue
                
            # If we can't find team IDs, log a warning but still try to create the innings
            if batting_team_id is None or bowling_team_id is None:
                # Attempt to get team IDs from the match record
                cursor.execute("""
                SELECT team1_id, team2_id FROM matches WHERE match_id = %s
                """, (match_id,))
                match_data = cursor.fetchone()
                
                if match_data:
                    team1_id, team2_id = match_data
                    # For inning 1, assume team1 is batting
                    if inning_number == 1:
                        batting_team_id = batting_team_id or team1_id
                        bowling_team_id = bowling_team_id or team2_id
                    # For inning 2, assume team2 is batting
                    elif inning_number == 2:
                        batting_team_id = batting_team_id or team2_id
                        bowling_team_id = bowling_team_id or team1_id
                    
                    print(f"Warning: Used match data to infer teams for match_id={match_id}, inning={inning_number}")
                else:
                    print(f"Error: Cannot create innings for match_id={match_id}, inning={inning_number} - missing team information")
                    continue
            
            inning_records.append((match_id, inning_number, batting_team_id, bowling_team_id))
        
        if inning_records:
            query = """
            INSERT INTO innings (match_id, inning_number, batting_team_id, bowling_team_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (match_id, inning_number) DO UPDATE 
            SET 
                batting_team_id = EXCLUDED.batting_team_id,
                bowling_team_id = EXCLUDED.bowling_team_id
            """
            
            execute_batch(cursor, query, inning_records, page_size=100)
        
        # Fetch the inserted innings with their IDs
        cursor.execute("SELECT inning_id, match_id, inning_number FROM innings;")
        innings_map = {(match_id, inning_num): inning_id for inning_id, match_id, inning_num in cursor.fetchall()}
        
        conn.commit()
        cursor.close()
        print(f"Successfully created/updated innings records. Total innings in database: {len(innings_map)}")
        return innings_map
    
    except Exception as e:
        conn.rollback()
        print(f"Error inserting innings: {e}")
        return {}
def handle_na_value(value):
    """Handle 'NA' string values in the dataset"""
    if pd.isna(value) or value == 'NA':
        return None
    return value

def insert_deliveries(conn, deliveries_df, innings_map, player_id_map):
    """Insert deliveries data into the database"""
    try:
        cursor = conn.cursor()
        
        delivery_records = []
        batch_size = 5000
        total_records = len(deliveries_df)
        
        for i, (_, row) in enumerate(deliveries_df.iterrows()):
            match_id = int(row['match_id']) if pd.notna(row['match_id']) else None
            inning_num = int(row['inning']) if pd.notna(row['inning']) else None
            inning_id = innings_map.get((match_id, inning_num), None)
            
            if not inning_id:
                print(f"Warning: No inning found for match_id={match_id}, inning={inning_num}")
                continue
            
            over_number = int(row['over']) if pd.notna(row['over']) else None
            ball_number = int(row['ball']) if pd.notna(row['ball']) else None
            
            # Handle player IDs
            batsman = handle_na_value(row['batter'])
            bowler = handle_na_value(row['bowler'])
            non_striker = handle_na_value(row['non_striker'])
            player_dismissed = handle_na_value(row['player_dismissed'])
            fielder = handle_na_value(row['fielder'])
            
            batsman_id = player_id_map.get(batsman, None) if batsman else None
            bowler_id = player_id_map.get(bowler, None) if bowler else None
            non_striker_id = player_id_map.get(non_striker, None) if non_striker else None
            player_dismissed_id = player_id_map.get(player_dismissed, None) if player_dismissed else None
            fielder_id = player_id_map.get(fielder, None) if fielder else None
            
            # Handle run values
            batsman_runs = int(row['batsman_runs']) if pd.notna(row['batsman_runs']) else 0
            extra_runs = int(row['extra_runs']) if pd.notna(row['extra_runs']) else 0
            total_runs = int(row['total_runs']) if pd.notna(row['total_runs']) else 0
            
            # Handle extras type
            extras_type = handle_na_value(row['extras_type'])
            
            # Handle wicket info
            is_wicket = bool(int(row['is_wicket'])) if pd.notna(row['is_wicket']) else False
            dismissal_kind = handle_na_value(row['dismissal_kind'])
            
            delivery_records.append((
                match_id, inning_id, over_number, ball_number,
                batsman_id, bowler_id, non_striker_id,
                batsman_runs, extra_runs, total_runs,
                extras_type, is_wicket, player_dismissed_id,
                dismissal_kind, fielder_id
            ))
            
            # Process in batches to avoid memory issues
            if (i+1) % batch_size == 0 or i == total_records - 1:
                query = """
                INSERT INTO deliveries (
                    match_id, inning_id, over_number, ball_number,
                    batsman_id, bowler_id, non_striker_id,
                    batsman_runs, extra_runs, total_runs,
                    extras_type, is_wicket, player_dismissed_id,
                    dismissal_kind, fielder_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
                """
                
                execute_batch(cursor, query, delivery_records, page_size=1000)
                delivery_records = []
                print(f"Processed {min(i+1, total_records)}/{total_records} deliveries")
        
        conn.commit()
        cursor.close()
        print(f"Successfully inserted deliveries data.")
    
    except Exception as e:
        conn.rollback()
        print(f"Error inserting deliveries: {e}")
def update_match_stats(conn):
    """Update the statistics tables after inserting all the basic data"""
    try:
        cursor = conn.cursor()
        
        # Update toss_stats table
        cursor.execute("""
        INSERT INTO toss_stats (team_id, season_id, toss_wins, chose_bat, chose_field, won_after_batting, won_after_fielding)
        SELECT 
            toss_winner_id as team_id, 
            season_id, 
            COUNT(*) as toss_wins,
            SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END) as chose_bat,
            SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END) as chose_field,
            SUM(CASE WHEN toss_decision = 'bat' AND winner_id = toss_winner_id THEN 1 ELSE 0 END) as won_after_batting,
            SUM(CASE WHEN toss_decision = 'field' AND winner_id = toss_winner_id THEN 1 ELSE 0 END) as won_after_fielding
        FROM 
            matches
        WHERE 
            toss_winner_id IS NOT NULL
        GROUP BY 
            toss_winner_id, season_id
        ON CONFLICT (team_id, season_id) DO UPDATE SET
            toss_wins = EXCLUDED.toss_wins,
            chose_bat = EXCLUDED.chose_bat,
            chose_field = EXCLUDED.chose_field,
            won_after_batting = EXCLUDED.won_after_batting,
            won_after_fielding = EXCLUDED.won_after_fielding;
        """)
        
        # Update head_to_head table
        cursor.execute("""
        INSERT INTO head_to_head (team1_id, team2_id, season_id, matches_played, team1_wins, team2_wins, no_results)
        WITH team_matchups AS (
            SELECT 
                CASE WHEN team1_id < team2_id THEN team1_id ELSE team2_id END as team1_id,
                CASE WHEN team1_id < team2_id THEN team2_id ELSE team1_id END as team2_id,
                season_id,
                COUNT(*) as matches_played,
                SUM(CASE 
                    WHEN (team1_id < team2_id AND winner_id = team1_id) OR 
                         (team1_id > team2_id AND winner_id = team2_id) 
                    THEN 1 ELSE 0 END) as team1_wins,
                SUM(CASE 
                    WHEN (team1_id < team2_id AND winner_id = team2_id) OR 
                         (team1_id > team2_id AND winner_id = team1_id) 
                    THEN 1 ELSE 0 END) as team2_wins,
                SUM(CASE WHEN winner_id IS NULL THEN 1 ELSE 0 END) as no_results
            FROM 
                matches
            WHERE 
                team1_id IS NOT NULL AND 
                team2_id IS NOT NULL
            GROUP BY 
                CASE WHEN team1_id < team2_id THEN team1_id ELSE team2_id END,
                CASE WHEN team1_id < team2_id THEN team2_id ELSE team1_id END,
                season_id
        )
        SELECT * FROM team_matchups
        ON CONFLICT (team1_id, team2_id, season_id) DO UPDATE SET
            matches_played = EXCLUDED.matches_played,
            team1_wins = EXCLUDED.team1_wins,
            team2_wins = EXCLUDED.team2_wins,
            no_results = EXCLUDED.no_results;
        """)
        
        # Update team_season_stats table - FIX COLUMN COUNT MISMATCH
        cursor.execute("""
        INSERT INTO team_season_stats (
            team_id, season_id, matches_played, matches_won,
            home_matches_played, home_matches_won,
            away_matches_played, away_matches_won,
            batting_first_played, batting_first_won,
            bowling_first_played, bowling_first_won
        )
        WITH team_seasons AS (
            -- Get all teams in each season
            SELECT DISTINCT m.team_id, m.season_id
            FROM (
                SELECT team1_id as team_id, season_id FROM matches WHERE team1_id IS NOT NULL
                UNION
                SELECT team2_id as team_id, season_id FROM matches WHERE team2_id IS NOT NULL
            ) m
            JOIN teams t ON m.team_id = t.team_id
            JOIN seasons s ON m.season_id = s.season_id
        ),
        team_stats AS (
            -- Calculate stats for each team in each season
            SELECT 
                ts.team_id,
                ts.season_id,
                -- Matches played
                COUNT(DISTINCT CASE WHEN m.team1_id = ts.team_id OR m.team2_id = ts.team_id THEN m.match_id END) as matches_played,
                -- Matches won
                COUNT(DISTINCT CASE WHEN m.winner_id = ts.team_id THEN m.match_id END) as matches_won,
                -- Home matches using venue as proxy
                COUNT(DISTINCT CASE 
                    WHEN (m.team1_id = ts.team_id AND v.venue_name = t.home_venue) OR 
                         (m.team2_id = ts.team_id AND v.venue_name = t.home_venue) 
                    THEN m.match_id END) as home_matches_played,
                -- Home matches won
                COUNT(DISTINCT CASE 
                    WHEN m.winner_id = ts.team_id AND 
                        ((m.team1_id = ts.team_id AND v.venue_name = t.home_venue) OR 
                         (m.team2_id = ts.team_id AND v.venue_name = t.home_venue))
                    THEN m.match_id END) as home_matches_won,
                -- Batting first
                COUNT(DISTINCT CASE 
                    WHEN (m.team1_id = ts.team_id AND m.toss_winner_id = ts.team_id AND m.toss_decision = 'bat') OR
                         (m.team2_id = ts.team_id AND m.toss_winner_id = ts.team_id AND m.toss_decision = 'bat') OR
                         (m.team1_id = ts.team_id AND m.toss_winner_id != ts.team_id AND m.toss_decision = 'field') OR
                         (m.team2_id = ts.team_id AND m.toss_winner_id != ts.team_id AND m.toss_decision = 'field')
                    THEN m.match_id END) as batting_first_played,
                -- Batting first and won
                COUNT(DISTINCT CASE 
                    WHEN m.winner_id = ts.team_id AND (
                        (m.team1_id = ts.team_id AND m.toss_winner_id = ts.team_id AND m.toss_decision = 'bat') OR
                        (m.team2_id = ts.team_id AND m.toss_winner_id = ts.team_id AND m.toss_decision = 'bat') OR
                        (m.team1_id = ts.team_id AND m.toss_winner_id != ts.team_id AND m.toss_decision = 'field') OR
                        (m.team2_id = ts.team_id AND m.toss_winner_id != ts.team_id AND m.toss_decision = 'field')
                    )
                    THEN m.match_id END) as batting_first_won
            FROM 
                team_seasons ts
                JOIN teams t ON ts.team_id = t.team_id
                LEFT JOIN matches m ON 
                    (m.team1_id = ts.team_id OR m.team2_id = ts.team_id) AND 
                    m.season_id = ts.season_id
                LEFT JOIN venues v ON m.venue_id = v.venue_id
            GROUP BY ts.team_id, ts.season_id
        )
        SELECT 
            team_id, 
            season_id, 
            matches_played, 
            matches_won,
            home_matches_played, 
            home_matches_won,
            matches_played - home_matches_played as away_matches_played,
            matches_won - home_matches_won as away_matches_won,
            batting_first_played, 
            batting_first_won,
            matches_played - batting_first_played as bowling_first_played,
            matches_won - batting_first_won as bowling_first_won
        FROM 
            team_stats
        ON CONFLICT (team_id, season_id) DO UPDATE SET
            matches_played = EXCLUDED.matches_played,
            matches_won = EXCLUDED.matches_won,
            home_matches_played = EXCLUDED.home_matches_played,
            home_matches_won = EXCLUDED.home_matches_won,
            away_matches_played = EXCLUDED.away_matches_played,
            away_matches_won = EXCLUDED.away_matches_won,
            batting_first_played = EXCLUDED.batting_first_played,
            batting_first_won = EXCLUDED.batting_first_won,
            bowling_first_played = EXCLUDED.bowling_first_played,
            bowling_first_won = EXCLUDED.bowling_first_won;
        """)
        
        conn.commit()
        cursor.close()
        print("Successfully updated statistics tables.")
    
    except Exception as e:
        conn.rollback()
        print(f"Error updating statistics: {e}")
def main():
    """Main function to execute the data import process"""
    try:
        # Step 1: Connect to database
        print("Step 1: Connecting to database...")
        conn = connect_to_db()
        if not conn:
            return
        
        # Step 2: Load data from CSV files
        print("\nStep 2: Loading data from CSV files...")
        matches_df, deliveries_df = load_data()
        if matches_df is None or deliveries_df is None:
            conn.close()
            return
        
        # Step 3: Extract unique data entities
        print("\nStep 3: Extracting unique data entities...")
        teams, team_short_names, venues, venue_city_map, seasons, season_year_map, players = extract_unique_data(
            matches_df, deliveries_df
        )
        
        # Step 4: Insert teams
        print("\nStep 4: Inserting teams...")
        team_id_map = insert_teams(conn, teams, team_short_names)
        
        # Step 5: Insert venues
        print("\nStep 5: Inserting venues...")
        venue_id_map = insert_venues(conn, venues, venue_city_map)
        
        # Step 6: Insert players
        print("\nStep 6: Inserting players...")
        player_id_map = insert_players(conn, players)
        
        # Step 7: Insert seasons
        print("\nStep 7: Inserting seasons...")
        season_id_map = insert_seasons(conn, seasons, season_year_map)
        
        # Step 8: Insert matches
        print("\nStep 8: Inserting matches...")
        insert_matches(conn, matches_df, team_id_map, venue_id_map, season_id_map, player_id_map)
        
        # Step 9: Insert innings
        print("\nStep 9: Inserting innings...")
        innings_map = insert_innings(conn, deliveries_df, team_id_map)
        
        # Step 10: Insert deliveries
        print("\nStep 10: Inserting deliveries...")
        insert_deliveries(conn, deliveries_df, innings_map, player_id_map)
        
        # Step 11: Update statistics tables
        print("\nStep 11: Updating statistics tables...")
        update_match_stats(conn)
        
        print("\nData import process completed successfully!")
        conn.close()
        
    except Exception as e:
        print(f"Error in data import process: {e}")

if __name__ == "__main__":
    main()