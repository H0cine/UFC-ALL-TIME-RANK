import pandas as pd
import numpy as np

ufcfights_not_sorted = pd.read_csv("ufc_all_fight_data.csv",index_col=0)
ufcfights = ufcfights_not_sorted.reset_index()

ufcfights = ufcfights.sort_index(ascending=False)

elo_ratings = {}
base_k_factor = 40
peak_elo_ratings = {}
INITIAL_RATING = 1000

unique_events = ufcfights[['event']].drop_duplicates().reset_index(drop=True)
unique_events['event_id'] = range(1, len(unique_events) + 1)
ufcfights = ufcfights.merge(unique_events, on='event')

ufcfights['method'] = ufcfights['method'].apply(lambda x: 'KO' if 'KO' in x else ('SUB' if 'SUB' in x else x))
ufcfights.drop(columns=["round", "time"], inplace=True)

def get_Kfactor(method,base_k=40):
     if method == 'KO' or method == 'SUB':
        return base_k * 1.15
     else:
         return base_k

def expected_score(rating1, rating2):
    return 1 / (1 + 10 ** ((rating2 - rating1) / 400))

def update_elo_rating(winner, loser, k_factor):
    expected_win = expected_score(winner, loser)
    new_winner_elo = winner + k_factor * (1 - expected_win)
    new_loser_elo = loser + k_factor * (0 - (1 - expected_win))
    return round(new_winner_elo, 2), round(new_loser_elo, 2)

ufcfights['cc_match'] = np.arange(1, len(ufcfights) + 1)

ufcfights['fighter_1_elo_start'] = 0
ufcfights['fighter_2_elo_start'] = 0
ufcfights['fighter_1_elo_end'] = 0
ufcfights['fighter_2_elo_end'] = 0

for index, row in ufcfights.iterrows():
    fighter_1 = row['fighter_1']
    fighter_2 = row['fighter_2']


    if fighter_1 not in elo_ratings:
        elo_ratings[fighter_1] = INITIAL_RATING
    if fighter_2 not in elo_ratings:
        elo_ratings[fighter_2] = INITIAL_RATING


    fighter_1_elo_start = elo_ratings[fighter_1]
    fighter_2_elo_start = elo_ratings[fighter_2]

    fight_method = row["method"]
    current_k = get_Kfactor(fight_method,base_k_factor)



    ufcfights.at[index, 'fighter_1_elo_start'] = fighter_1_elo_start
    ufcfights.at[index, 'fighter_2_elo_start'] = fighter_2_elo_start

    # Update Elo based on the result
    if row['result'] == 'win':  # Fighter 1 wins
        new_fighter1_elo, new_fighter2_elo = update_elo_rating(fighter_1_elo_start, fighter_2_elo_start, current_k)
    elif row["result"] == 'draw': 
        new_fighter1_elo, new_fighter2_elo = update_elo_rating(fighter_1_elo_start, fighter_2_elo_start, current_k / 2)
    else:  # No contest
        new_fighter1_elo, new_fighter2_elo = fighter_1_elo_start, fighter_2_elo_start
    
    if fighter_1 not in peak_elo_ratings or new_fighter1_elo > peak_elo_ratings[fighter_1]:
        peak_elo_ratings[fighter_1] = new_fighter1_elo
    if fighter_2 not in peak_elo_ratings or new_fighter2_elo > peak_elo_ratings[fighter_2]:
        peak_elo_ratings[fighter_2] = new_fighter2_elo


    ufcfights.at[index, 'fighter_1_elo_end'] = new_fighter1_elo
    ufcfights.at[index, 'fighter_2_elo_end'] = new_fighter2_elo

    elo_ratings[fighter_1] = new_fighter1_elo
    elo_ratings[fighter_2] = new_fighter2_elo


def get_fighter_info(fighter_name, elo_ratings, ufcfights, initial_elo=1000):
    if fighter_name in elo_ratings:
        elo = elo_ratings["fighter_name"]
    else:
        elo = initial_elo
    
    # Find all matches where the fighter appeared as either fighter_1 or fighter_2
    fighter_matches = ufcfights[(ufcfights['fighter_1'] == fighter_name) | (ufcfights['fighter_2'] == fighter_name)]
    
    if not fighter_matches.empty:
        print(f"{fighter_name}'s current Elo rating: {elo}\n")
        print(f"{fighter_name}'s matches:")
        return fighter_matches[['event', 'fighter_1', 'fighter_2', 'result', 'fighter_1_elo_start', 'fighter_2_elo_start','fighter_1_elo_end','fighter_2_elo_end']]
    else:
        return f"{fighter_name} has no recorded matches."



def get_ranking():
    ranking = sorted(elo_ratings.items(), key=lambda x: x[1], reverse=True)
    return [{"fighter": fighter, "rating": rating} for fighter, rating in ranking]



ranking = get_ranking()

df = pd.DataFrame(ranking)
df.to_csv("ufc_new_rankings.csv", index=False)

print("Fighter rankings saved to ufc_rankings.csv")
