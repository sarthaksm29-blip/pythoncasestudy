import pandas as pd
import random
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from functools import wraps


def create_initial_data(voters_filename='voters.csv', candidates_filename='candidates.txt', total_voters=500):
    """
    Create some dummy voters and candidates so that the system can run.
    This just writes out:
    - voters.csv   -> Voter_ID, Status
    - candidates.txt -> one candidate name per line
    """

    # make a simple voters list
    voters = []
    for i in range(1, total_voters + 1):
        voter_id = f"VOTER{i:03d}"
        status = "Registered"
        voters.append([voter_id, status])

    # write voters file
    with open(voters_filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Voter_ID", "Status"])
        writer.writerows(voters)

    # just hardcoding 3 candidates for now
    candidates = ["Alice Kumar", "Bob Singh", "Charlie Patel"]
    with open(candidates_filename, "w") as f:
        for name in candidates:
            f.write(name + "\n")


# decorator for confirming vote (sort of "automation" feature)
def voting_confirmation(func):
    """
    Wrapper that prints a confirmation message only when the vote succeeds.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if result:
            print(f"✨ CONFIRMED: Vote for {args[2]} successfully logged by {args[1]}.")
        return result

    return wrapper

class Candidate:
    """
    Represents a single candidate and keeps track of their vote count.
    """

    def __init__(self, name):
        self.name = name
        self._vote_count = 0

    def add_vote(self):
        self._vote_count += 1

    def get_vote_count(self):
        return self._vote_count


class Election:
    """
    Handles:
    - reading voters and candidates
    - casting votes (with checks)
    - computing results
    """

    def __init__(self, name, candidates_file, voters_file):
        self.name = name
        self.voting_period = None
        self.candidates = {}  # name -> Candidate object

        # load voters from CSV
        self.eligible_voters = pd.read_csv(voters_file)
        self.voted_voters = set()

        self.total_eligible_voters = len(self.eligible_voters)
        self.total_votes_cast = 0

        self._load_candidates(candidates_file)

    def _load_candidates(self, filename):
        """
        Read candidates from the text file and create Candidate objects.
        """
        try:
            with open(filename, "r") as f:
                for line in f:
                    name = line.strip()
                    if name:
                        self.candidates[name] = Candidate(name)
        except FileNotFoundError:
            print(f"Error: Candidate file {filename} not found.")

    def set_voting_period(self, start_date_str, end_date_str):
        """
        Set the voting period. Example: 'Oct 12' to 'Oct 14'
        This is more for display; we are not enforcing dates in code.
        """
        date_format = "%b %d"
        try:
            start_date = datetime.strptime(start_date_str, date_format)
            end_date = datetime.strptime(end_date_str, date_format)
            self.voting_period = (start_date, end_date)
        except ValueError:
            print("Error: Date format should be like 'Oct 12'.")

    @voting_confirmation
    def cast_vote(self, voter_id, candidate_name):
        """
        Cast a vote:
        - checks if voter is in the eligible list
        - prevents double voting
        - checks if candidate exists
        Returns True if vote was recorded, False otherwise.
        """

        # check voter is registered
        if voter_id not in self.eligible_voters["Voter_ID"].values:
            print(f"🗳️ VOTE REJECTED: Voter ID {voter_id} is not eligible.")
            return False

        # prevent duplicates
        if voter_id in self.voted_voters:
            print(f"🗳️ VOTE REJECTED: Voter ID {voter_id} has already cast a vote.")
            return False

        # check candidate name
        if candidate_name not in self.candidates:
            print(f"🗳️ VOTE REJECTED: Candidate '{candidate_name}' is not running.")
            return False

        # if everything is fine, record the vote
        self.candidates[candidate_name].add_vote()
        self.voted_voters.add(voter_id)
        self.total_votes_cast += 1

        return True

    # simple lambda to compute turnout (%)
    calculate_turnout = lambda self: (self.total_votes_cast / self.total_eligible_voters) * 100 if self.total_eligible_voters > 0 else 0

    def generate_results(self):
        """
        Build a DataFrame with:
        - Candidate
        - Votes
        - Percentage
        Also returns winner, turnout and abstentions.
        """

        data = []
        for name, candidate in self.candidates.items():
            votes = candidate.get_vote_count()
            if self.total_votes_cast > 0:
                percentage = (votes / self.total_votes_cast) * 100
            else:
                percentage = 0
            data.append([name, votes, percentage])

        results_df = pd.DataFrame(data, columns=["Candidate", "Votes", "Percentage"])
        results_df = results_df.sort_values(by="Votes", ascending=False).reset_index(drop=True)

        if not results_df.empty:
            winner_row = results_df.iloc[0]
            winner_name = winner_row["Candidate"]
            winner_percent = winner_row["Percentage"]
        else:
            winner_name = "N/A"
            winner_percent = 0.0

        turnout_value = self.calculate_turnout()
        abstentions = self.total_eligible_voters - self.total_votes_cast

        return {
            "results_df": results_df,
            "winner": (winner_name, winner_percent),
            "turnout": turnout_value,
            "abstentions": abstentions
        }

def plot_results(results_df, election_name, total_votes_cast):
    """
    Make a bar chart and pie chart from the results DataFrame.
    """

    # Bar chart for number of votes
    plt.figure(figsize=(10, 6))
    plt.bar(results_df["Candidate"], results_df["Votes"], color=["teal", "skyblue", "salmon"])
    plt.xlabel("Candidate")
    plt.ylabel("Number of Votes")
    plt.title(f"Vote Distribution Comparison for {election_name}")

    # show the percentage above each bar
    for i, row in results_df.iterrows():
        plt.text(i, row["Votes"] + 5, f"{row['Percentage']:.1f}%", ha="center")

    plt.grid(axis="y", linestyle="--")
    plt.show()

    # Pie chart for vote percentages
    plt.figure(figsize=(8, 8))
    plt.pie(
        results_df["Votes"],
        labels=results_df["Candidate"],
        autopct="%1.1f%%",
        startangle=90,
        colors=["teal", "skyblue", "salmon"],
        explode=(0.05, 0, 0)
    )
    plt.title(f"Overall Vote Share ({total_votes_cast} Votes Cast)")
    plt.show()

def main():
    """
    Main driver function:
    - creates data
    - runs a simulated election (fixed distribution)
    - prints report
    - generates charts
    """

    VOTERS_FILE = "voters.csv"
    CANDIDATES_FILE = "candidates.txt"

    # 1. Setup
    print("--- 1. Setting Up Election Data ---")
    create_initial_data(voters_filename=VOTERS_FILE, candidates_filename=CANDIDATES_FILE)

    council_election = Election(
        name="Student Council President",
        candidates_file=CANDIDATES_FILE,
        voters_file=VOTERS_FILE
    )
    council_election.set_voting_period(start_date_str="Oct 12", end_date_str="Oct 14")

    # 2. Simulate votes (450 total: 200 Alice, 150 Bob, 100 Charlie)
    print("\n--- 2. Starting Vote Casting Simulation ---")

    voter_ids = council_election.eligible_voters["Voter_ID"].tolist()

    vote_targets = {
        "Alice Kumar": 200,
        "Bob Singh": 150,
        "Charlie Patel": 100
    }

    # create a list like ["Alice", "Alice", ..., "Bob", ...]
    vote_list = []
    for candidate_name, count in vote_targets.items():
        for _ in range(count):
            vote_list.append(candidate_name)

    random.shuffle(vote_list)

    voters_to_cast = voter_ids[:450]

    print("Casting votes (showing confirmation for first 5):")
    for i, (voter_id, candidate_name) in enumerate(zip(voters_to_cast, vote_list)):
        if i < 5:
            # normal decorated call (prints confirmation on success)
            council_election.cast_vote(voter_id, candidate_name)
        else:
            # call the original function without decorator to avoid spammy output
            council_election.cast_vote.__wrapped__(council_election, voter_id, candidate_name)

    # 3. Final results and summary
    final_results = council_election.generate_results()
    results_df = final_results["results_df"]
    winner_name, winner_percent = final_results["winner"]

    print("\n--- 3. Final Election Report ---")
    print("\n--- VOTING STATUS ---")
    print(f"Total Eligible Voters: {council_election.total_eligible_voters}")
    print(f"Votes Cast: {council_election.total_votes_cast} ({final_results['turnout']:.1f}% participation)")
    print("Voting Period: Active (Polls Close: Oct 14, 5:00 PM)")

    print("\n--- LIVE RESULTS TABLE ---")
    # to_markdown needs 'tabulate' installed: pip install tabulate
    print(results_df.to_markdown(index=False, floatfmt=".1f"))

    print("\n--- ELECTION METRICS ---")
    print(f"Voter Turnout: {final_results['turnout']:.1f}%")
    print(f"PROVISIONAL WINNER: {winner_name} with {winner_percent:.1f}% of votes.")
    print("INVALID VOTES: 0 (Prevented by the system guardrails)")
    print(f"ABSTENTIONS: {final_results['abstentions']}")

    # 4. Charts
    print("\n--- 4. Generating Result Charts ---")
    plot_results(results_df, council_election.name, council_election.total_votes_cast)


if __name__ == "__main__":
    main()

