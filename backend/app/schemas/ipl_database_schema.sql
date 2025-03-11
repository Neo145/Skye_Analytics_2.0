-- Connect to the database first
\c ipl_2008_2024;

-- Create teams table
CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    team_name VARCHAR(100) UNIQUE NOT NULL,
    team_short_name VARCHAR(10),
    home_venue VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create venues table
CREATE TABLE venues (
    venue_id SERIAL PRIMARY KEY,
    venue_name VARCHAR(200) UNIQUE NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    capacity INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create players table
CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    country VARCHAR(100),
    playing_role VARCHAR(50),
    batting_style VARCHAR(50),
    bowling_style VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create seasons table
CREATE TABLE seasons (
    season_id SERIAL PRIMARY KEY,
    season_name VARCHAR(50) UNIQUE NOT NULL,
    season_year INTEGER,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create matches table with appropriate foreign keys
CREATE TABLE matches (
    match_id INTEGER PRIMARY KEY,
    season_id INTEGER REFERENCES seasons(season_id),
    match_date DATE NOT NULL,
    venue_id INTEGER REFERENCES venues(venue_id),
    team1_id INTEGER REFERENCES teams(team_id),
    team2_id INTEGER REFERENCES teams(team_id),
    toss_winner_id INTEGER REFERENCES teams(team_id),
    toss_decision VARCHAR(10) CHECK (toss_decision IN ('bat', 'field')),
    winner_id INTEGER REFERENCES teams(team_id),
    result VARCHAR(20),
    result_margin NUMERIC(10, 2),
    player_of_match_id INTEGER REFERENCES players(player_id),
    match_type VARCHAR(20),
    target_runs NUMERIC(10, 2),
    target_overs NUMERIC(5, 1),
    is_super_over BOOLEAN DEFAULT FALSE,
    dl_method VARCHAR(10),
    umpire1 VARCHAR(100),
    umpire2 VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create team_players table for tracking players in teams across seasons
CREATE TABLE team_players (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(team_id),
    player_id INTEGER REFERENCES players(player_id),
    season_id INTEGER REFERENCES seasons(season_id),
    is_captain BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (team_id, player_id, season_id)
);

-- Create innings table
CREATE TABLE innings (
    inning_id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(match_id),
    inning_number INTEGER CHECK (inning_number IN (1, 2, 3, 4)), -- Allow for super overs
    batting_team_id INTEGER REFERENCES teams(team_id),
    bowling_team_id INTEGER REFERENCES teams(team_id),
    total_runs INTEGER,
    total_wickets INTEGER,
    total_overs NUMERIC(5, 1),
    extras INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (match_id, inning_number)
);

-- Create deliveries table with detailed ball-by-ball information
CREATE TABLE deliveries (
    delivery_id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(match_id),
    inning_id INTEGER REFERENCES innings(inning_id),
    over_number INTEGER,
    ball_number INTEGER,
    batsman_id INTEGER REFERENCES players(player_id),
    bowler_id INTEGER REFERENCES players(player_id),
    non_striker_id INTEGER REFERENCES players(player_id),
    batsman_runs INTEGER,
    extra_runs INTEGER,
    total_runs INTEGER,
    extras_type VARCHAR(20) CHECK (extras_type IN ('wides', 'noballs', 'byes', 'legbyes', NULL)),
    is_wicket BOOLEAN DEFAULT FALSE,
    player_dismissed_id INTEGER REFERENCES players(player_id),
    dismissal_kind VARCHAR(50),
    fielder_id INTEGER REFERENCES players(player_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create head_to_head table to optimize head-to-head queries
CREATE TABLE head_to_head (
    id SERIAL PRIMARY KEY,
    team1_id INTEGER REFERENCES teams(team_id),
    team2_id INTEGER REFERENCES teams(team_id),
    season_id INTEGER REFERENCES seasons(season_id),
    matches_played INTEGER DEFAULT 0,
    team1_wins INTEGER DEFAULT 0,
    team2_wins INTEGER DEFAULT 0,
    no_results INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (team1_id, team2_id, season_id)
);

-- Create toss_stats table for optimizing toss analysis queries
CREATE TABLE toss_stats (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(team_id),
    season_id INTEGER REFERENCES seasons(season_id),
    toss_wins INTEGER DEFAULT 0,
    chose_bat INTEGER DEFAULT 0,
    chose_field INTEGER DEFAULT 0,
    won_after_batting INTEGER DEFAULT 0,
    won_after_fielding INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (team_id, season_id)
);

-- Create venue_stats table for optimizing venue analysis
CREATE TABLE venue_stats (
    id SERIAL PRIMARY KEY,
    venue_id INTEGER REFERENCES venues(venue_id),
    season_id INTEGER REFERENCES seasons(season_id),
    matches_played INTEGER DEFAULT 0,
    batting_first_wins INTEGER DEFAULT 0,
    batting_second_wins INTEGER DEFAULT 0,
    avg_first_innings_score INTEGER DEFAULT 0,
    avg_second_innings_score INTEGER DEFAULT 0,
    highest_total INTEGER DEFAULT 0,
    lowest_total INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (venue_id, season_id)
);

-- Create team_season_stats for optimizing team performance analysis
CREATE TABLE team_season_stats (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(team_id),
    season_id INTEGER REFERENCES seasons(season_id),
    matches_played INTEGER DEFAULT 0,
    matches_won INTEGER DEFAULT 0,
    home_matches_played INTEGER DEFAULT 0,
    home_matches_won INTEGER DEFAULT 0,
    away_matches_played INTEGER DEFAULT 0,
    away_matches_won INTEGER DEFAULT 0,
    batting_first_played INTEGER DEFAULT 0,
    batting_first_won INTEGER DEFAULT 0,
    bowling_first_played INTEGER DEFAULT 0,
    bowling_first_won INTEGER DEFAULT 0,
    total_runs_scored INTEGER DEFAULT 0,
    total_balls_faced INTEGER DEFAULT 0,
    total_runs_conceded INTEGER DEFAULT 0,
    total_balls_bowled INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (team_id, season_id)
);

-- Create player_season_stats for player performance analysis
CREATE TABLE player_season_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(player_id),
    team_id INTEGER REFERENCES teams(team_id),
    season_id INTEGER REFERENCES seasons(season_id),
    -- Batting stats
    matches_played INTEGER DEFAULT 0,
    innings_batted INTEGER DEFAULT 0,
    runs_scored INTEGER DEFAULT 0,
    balls_faced INTEGER DEFAULT 0,
    fours INTEGER DEFAULT 0,
    sixes INTEGER DEFAULT 0,
    highest_score INTEGER DEFAULT 0,
    fifties INTEGER DEFAULT 0,
    hundreds INTEGER DEFAULT 0,
    not_outs INTEGER DEFAULT 0,
    -- Bowling stats
    innings_bowled INTEGER DEFAULT 0,
    overs_bowled NUMERIC(10, 1) DEFAULT 0,
    runs_conceded INTEGER DEFAULT 0,
    wickets INTEGER DEFAULT 0,
    maidens INTEGER DEFAULT 0,
    economy NUMERIC(5, 2) DEFAULT 0,
    best_bowling_figures VARCHAR(10),
    -- Fielding stats
    catches INTEGER DEFAULT 0,
    stumpings INTEGER DEFAULT 0,
    run_outs INTEGER DEFAULT 0,
    -- Overall
    player_of_match_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (player_id, team_id, season_id)
);

-- Create indexes for performance optimization

-- Indexes for matches table
CREATE INDEX idx_matches_season ON matches(season_id);
CREATE INDEX idx_matches_venue ON matches(venue_id);
CREATE INDEX idx_matches_teams ON matches(team1_id, team2_id);
CREATE INDEX idx_matches_winner ON matches(winner_id);
CREATE INDEX idx_matches_date ON matches(match_date);

-- Indexes for deliveries table
CREATE INDEX idx_deliveries_match ON deliveries(match_id);
CREATE INDEX idx_deliveries_inning ON deliveries(inning_id);
CREATE INDEX idx_deliveries_batsman ON deliveries(batsman_id);
CREATE INDEX idx_deliveries_bowler ON deliveries(bowler_id);
CREATE INDEX idx_deliveries_wicket ON deliveries(is_wicket, dismissal_kind);

-- Indexes for innings table
CREATE INDEX idx_innings_match ON innings(match_id);
CREATE INDEX idx_innings_teams ON innings(batting_team_id, bowling_team_id);

-- Indexes for team_players table
CREATE INDEX idx_team_players_team ON team_players(team_id);
CREATE INDEX idx_team_players_player ON team_players(player_id);
CREATE INDEX idx_team_players_season ON team_players(season_id);

-- Indexes for head_to_head table
CREATE INDEX idx_h2h_teams ON head_to_head(team1_id, team2_id);
CREATE INDEX idx_h2h_season ON head_to_head(season_id);

-- Indexes for toss_stats table
CREATE INDEX idx_toss_team ON toss_stats(team_id);
CREATE INDEX idx_toss_season ON toss_stats(season_id);

-- Indexes for venue_stats table
CREATE INDEX idx_venue_stats_venue ON venue_stats(venue_id);
CREATE INDEX idx_venue_stats_season ON venue_stats(season_id);

-- Indexes for team_season_stats table
CREATE INDEX idx_team_season_team ON team_season_stats(team_id);
CREATE INDEX idx_team_season_season ON team_season_stats(season_id);

-- Indexes for player_season_stats table
CREATE INDEX idx_player_season_player ON player_season_stats(player_id);
CREATE INDEX idx_player_season_team ON player_season_stats(team_id);
CREATE INDEX idx_player_season_season ON player_season_stats(season_id);