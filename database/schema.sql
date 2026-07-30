CREATE TABLE publications (
    handle TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    doi TEXT UNIQUE,
    year INTEGER,
    type TEXT,
    type_driver TEXT,
    venue TEXT,
    url TEXT,
    last_update BIGINT,

    insert_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE authors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,

    insert_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE
);


CREATE TABLE publications_authors (
    publication_handle TEXT NOT NULL,
    author_id TEXT NOT NULL,

    insert_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE,

    PRIMARY KEY (publication_handle, author_id),

    FOREIGN KEY (publication_handle)
        REFERENCES publications(handle)
        ON DELETE CASCADE,

    FOREIGN KEY (author_id)
        REFERENCES authors(id)
        ON DELETE CASCADE
);

CREATE TABLE keywords (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,

    insert_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE publications_keywords (
    publication_handle TEXT NOT NULL,
    keyword_id INTEGER NOT NULL,

    insert_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE,

    PRIMARY KEY (publication_handle, keyword_id),

    FOREIGN KEY (publication_handle)
        REFERENCES publications(handle)
        ON DELETE CASCADE,

    FOREIGN KEY (keyword_id)
        REFERENCES keywords(id)
        ON DELETE CASCADE
);