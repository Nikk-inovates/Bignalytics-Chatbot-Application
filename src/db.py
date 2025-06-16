async def save_chat(pool, question, answer, timestamp):
    query = """
    INSERT INTO chat_logs (question, answer, timestamp)
    VALUES ($1, $2, $3)
    """
    await pool.execute(query, question, answer, timestamp)

async def save_feedback(pool, question, answer, rating, comment, timestamp):
    # Ensure rating is either 'thumbs up' or 'thumbs down'
    assert rating in ("up","down"), "Invalid rating value"
    query = """
    INSERT INTO feedback_logs (question, answer, rating, comment, timestamp)
    VALUES ($1, $2, $3, $4, $5)
    """
    await pool.execute(query, question, answer, rating, comment, timestamp)
