import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Database connection parameters
DB_PARAMS = {
    'dbname': 'ipl_2008_2024',
    'user': 'skye',
    'host': 'localhost',
    'password': 'skye'
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
        deliveries_df = pd.read_csv('F:/Skye_analytics_2.0/backend/data/deliveries.csv')
        return deliveries_df
    except Exception as e:
        print(f"Error loading CSV files: {e}")
        return None

def fix_innings_table(conn):
    """Create innings records for all matches"""
    try:
        cursor = conn.cursor()
        
        # Check current state
        cursor.execute("SELECT COUNT(*) FROM innings")
        innings_count = cursor.fetchone()[0]
        print(f"Current innings count: {innings_count}")
        
        # Create first innings (team1 batting, team2 bowling)
        cursor.execute("""
        INSERT INTO innings (match_id, inning_number, batting_team_id, bowling_team_id)
        SELECT m.match_id, 1, m.team1_id, m.team2_id
        FROM matches m
        WHERE NOT EXISTS (
            SELECT 1 FROM innings i 
            WHERE i.match_id = m.match_id AND i.inning_number = 1
        )
        RETURNING match_id
        """)
        
        first_innings_matches = cursor.fetchall()
        print(f"Created {len(first_innings_matches)} first innings records")
        
        # Create second innings (team2 batting, team1 bowling)
        cursor.execute("""
        INSERT INTO innings (match_id, inning_number, batting_team_id, bowling_team_id)
        SELECT m.match_id, 2, m.team2_id, m.team1_id
        FROM matches m
        WHERE NOT EXISTS (
            SELECT 1 FROM innings i 
            WHERE i.match_id = m.match_id AND i.inning_number = 2
        )
        RETURNING match_id
        """)
        
        second_innings_matches = cursor.fetchall()
        print(f"Created {len(second_innings_matches)} second innings records")
        
        # Check if we have matches with swapped batting order (team2 batting first)
        # If we have deliveries data, we'll fix this later based on deliveries
        
        conn.commit()
        cursor.close()
        print("Successfully fixed innings table!")
        return True
    
    except Exception as e:
        conn.rollback()
        print(f"Error fixing innings table: {e}")
        return False

def handle_na_value(value):
    """Handle 'NA' string values in the dataset"""
    if pd.isna(value) or value == 'NA':
        return None
    return value

def get_team_player_maps(conn):
    """Get mapping dictionaries for teams and players"""
    try:
        cursor = conn.cursor()
        
        # Get team mapping
        cursor.execute("SELECT team_id, team_name FROM teams")
        team_id_map = {name: id for id, name in cursor.fetchall()}
        
        # Get player mapping
        cursor.execute("SELECT player_id, player_name FROM players")
        player_id_map = {name: id for id, name in cursor.fetchall()}
        
        cursor.close()
        return team_id_map, player_id_map
    
    except Exception as e:
        print(f"Error getting mapping data: {e}")
        return {}, {}

def get_innings_map(conn):
    """Get mapping for innings (match_id, inning_number) -> inning_id"""
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT inning_id, match_id, inning_number FROM innings")
        innings_map = {(match_id, inning_num): inning_id for inning_id, match_id, inning_num in cursor.fetchall()}
        
        cursor.close()
        return innings_map
    
    except Exception as e:
        print(f"Error getting innings mapping: {e}")
        return {}

def insert_deliveries(conn, deliveries_df, innings_map, player_id_map):
    """Insert deliveries data into the database with improved error handling"""
    try:
        cursor = conn.cursor()
        
        # Check if deliveries table has data
        cursor.execute("SELECT COUNT(*) FROM deliveries")
        deliveries_count = cursor.fetchone()[0]
        
        if deliveries_count > 0:
            print(f"Deliveries table already has {deliveries_count} records.")
            return
        
        print(f"Beginning deliveries import. Total rows: {len(deliveries_df)}")
        
        delivery_records = []
        batch_size = 5000
        total_records = len(deliveries_df)
        processed = 0
        skipped = 0
        start_time = time.time()
        
        for i, (_, row) in enumerate(deliveries_df.iterrows()):
            match_id = int(row['match_id']) if pd.notna(row['match_id']) else None
            inning_num = int(row['inning']) if pd.notna(row['inning']) else None
            inning_id = innings_map.get((match_id, inning_num), None)
            
            if not inning_id:
                skipped += 1
                if skipped <= 10 or skipped % 1000 == 0:
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
                processed += len(delivery_records)
                delivery_records = []
                
                elapsed = time.time() - start_time
                progress = (i+1) / total_records * 100
                remaining = elapsed / (i+1) * (total_records - i - 1) if i > 0 else 0
                
                print(f"Progress: {progress:.1f}% ({processed} records) - ETA: {remaining/60:.1f} minutes")
        
        conn.commit()
        cursor.close()
        
        print(f"Successfully inserted {processed} deliveries.")
        print(f"Skipped {skipped} deliveries due to missing innings.")
        print(f"Total time: {(time.time() - start_time)/60:.2f} minutes")
        return True
    
    except Exception as e:
        conn.rollback()
        print(f"Error inserting deliveries: {e}")
        return False

def update_innings_statistics(conn):
    """Update statistics in innings table based on deliveries"""
    try:
        cursor = conn.cursor()
        
        # Update runs and wickets in innings
        cursor.execute("""
        UPDATE innings i SET
            total_runs = d.runs,
            total_wickets = d.wickets,
            extras = d.extras,
            total_overs = FLOOR(d.balls / 6) + (d.balls % 6) * 0.1
        FROM (
            SELECT inning_id,
                   SUM(total_runs) as runs,
                   SUM(CASE WHEN is_wicket THEN 1 ELSE 0 END) as wickets,
                   SUM(extra_runs) as extras,
                   COUNT(*) as balls
            FROM deliveries
            GROUP BY inning_id
        ) d
        WHERE i.inning_id = d.inning_id
        """)
        
        updated_rows = cursor.rowcount
        print(f"Updated statistics for {updated_rows} innings.")
        
        conn.commit()
        cursor.close()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating innings statistics: {e}")
        return False

def update_match_stats(conn):
    """Update the statistics tables after fixing the data"""
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
        
        print("Toss statistics updated successfully.")
        
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
        
        print("Head-to-head statistics updated successfully.")
        
        # Update team_season_stats table with correct column names in INSERT
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
        
        print("Team season statistics updated successfully.")
        
        conn.commit()
        cursor.close()
        print("Successfully updated all statistics tables.")
        return True
    
    except Exception as e:
        conn.rollback()
        print(f"Error updating statistics: {e}")
        return False

def verify_data_integrity(conn):
    """Verify that the database is in good shape after repair"""
    try:
        cursor = conn.cursor()
        
        # Check table counts
        cursor.execute("""
        SELECT 'teams' as table_name, COUNT(*) as record_count FROM teams
        UNION ALL
        SELECT 'venues', COUNT(*) FROM venues
        UNION ALL
        SELECT 'players', COUNT(*) FROM players
        UNION ALL
        SELECT 'seasons', COUNT(*) FROM seasons
        UNION ALL
        SELECT 'matches', COUNT(*) FROM matches
        UNION ALL
        SELECT 'innings', COUNT(*) FROM innings
        UNION ALL
        SELECT 'deliveries', COUNT(*) FROM deliveries
        UNION ALL
        SELECT 'toss_stats', COUNT(*) FROM toss_stats
        UNION ALL
        SELECT 'head_to_head', COUNT(*) FROM head_to_head
        UNION ALL
        SELECT 'team_season_stats', COUNT(*) FROM team_season_stats;
        """)
        
        results = cursor.fetchall()
        print("\nDatabase table counts after repair:")
        for table, count in results:
            print(f"{table}: {count:,} records")
        
        # Check innings-to-deliveries relationship
        cursor.execute("""
        SELECT COUNT(*) as total_innings, 
               COUNT(CASE WHEN d.count > 0 THEN 1 END) as innings_with_deliveries,
               COUNT(CASE WHEN d.count = 0 OR d.count IS NULL THEN 1 END) as innings_without_deliveries
        FROM innings i
        LEFT JOIN (
            SELECT inning_id, COUNT(*) as count 
            FROM deliveries 
            GROUP BY inning_id
        ) d ON i.inning_id = d.inning_id;
        """)
        
        total, with_deliveries, without_deliveries = cursor.fetchone()
        print(f"\nInnings analysis:")
        print(f"Total innings: {total:,}")
        print(f"Innings with deliveries: {with_deliveries:,}")
        print(f"Innings without deliveries: {without_deliveries:,}")
        
        # Check for any anomalies
        if without_deliveries > 0:
            print(f"\nWarning: {without_deliveries} innings have no deliveries.")
        
        cursor.close()
        print("\nDatabase integrity check completed.")
        return True
        
    except Exception as e:
        print(f"Error during integrity check: {e}")
        return False

def main():
    """Main function to repair the database"""
    try:
        print("=== IPL Database Repair Tool ===")
        print("This script will fix issues with innings and deliveries tables.")
        
        # Step 1: Connect to database
        print("\nStep 1: Connecting to database...")
        conn = connect_to_db()
        if not conn:
            return
        
        # Step 2: Fix innings table
        print("\nStep 2: Fixing innings table...")
        if not fix_innings_table(conn):
            conn.close()
            return
        
        # Step 3: Load deliveries data
        print("\nStep 3: Loading deliveries data...")
        deliveries_df = load_data()
        if deliveries_df is None:
            conn.close()
            return
            
        # Step 4: Get mapping data
        print("\nStep 4: Getting mapping data...")
        team_id_map, player_id_map = get_team_player_maps(conn)
        innings_map = get_innings_map(conn)
        
        # Step 5: Insert deliveries
        print("\nStep 5: Inserting deliveries data...")
        if not insert_deliveries(conn, deliveries_df, innings_map, player_id_map):
            conn.close()
            return
        
        # Step 6: Update innings statistics
        print("\nStep 6: Updating innings statistics...")
        if not update_innings_statistics(conn):
            conn.close()
            return
        
        # Step 7: Update statistics tables
        print("\nStep 7: Updating statistics tables...")
        if not update_match_stats(conn):
            conn.close()
            return
        
        # Step 8: Verify data integrity
        print("\nStep 8: Verifying data integrity...")
        verify_data_integrity(conn)
        
        print("\nDatabase repair completed successfully!")
        conn.close()
        
    except Exception as e:
        print(f"Error in database repair process: {e}")

if __name__ == "__main__":
    main()