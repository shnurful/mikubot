import sqlite3
import random

def generate_markov_text(db_path: str ="./db/bot.db", max_words: int =100) -> str | None:
    """
    Connects to the database, builds a Markov chain based on 2-word prefixes,
    and generates random text.
    """
    try:
        # Connect to database and fetch messages
        # Equivalent to db.InitDB and the SELECT query in main.go
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM messages")
            # Fetch all rows and extract the content string (column 0)
            messages = [row[0] for row in cursor.fetchall()]

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return

    # Data structures to replace Go's map[wordpair][]string
    # Key is a tuple (w1, w2), Value is a list of next possible words
    tokens = {}
    all_keys = []

    # Build the possible next word table
    m: str
    for m in messages:
        w1, w2 = "", ""  # Reset state for each message
        
        # Split message into words (Python's split handles whitespace automatically)
        words: list[str] = m.split()
        
        for w in words:
            key = (w1, w2)
            
            if key not in tokens:
                tokens[key] = []
            
            tokens[key].append(w)
            all_keys.append(key)
            
            # Shift the window
            w1, w2 = w2, w

    if not all_keys:
        print("No keys found to generate text.")
        return 

    # Get starter key (replicates rand_key := keys[rand.Intn(len(keys))])
    rand_key = random.choice(all_keys)
    
    # Set up output
    # Note: Strings are immutable in Python, but this matches the logic of the Go string concat
    current_w1, current_w2 = rand_key
    output = current_w1 + " " + current_w2
    
    count = 0
    while count < max_words:
        # Check if the current pair exists in our map and has followers
        if rand_key not in tokens or not tokens[rand_key]:
            break
        
        # Pick next word randomly
        possibles = tokens[rand_key]
        next_word = random.choice(possibles)
        
        # Shift the key: (old_w2, next_word)
        rand_key = (rand_key[1], next_word)
        
        output += " " + next_word
        count += 1
    
    return output 

if __name__ == "__main__":
    _ = generate_markov_text()
