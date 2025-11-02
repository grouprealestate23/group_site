-- schema.sql
DROP TABLE IF EXISTS conversations;

CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_question TEXT NOT NULL,
    bot_answer TEXT NOT NULL,
    session_id TEXT -- Για μελλοντική χρήση
);