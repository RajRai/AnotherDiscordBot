from tbot.dbops import connectToDB as create_connection
from sqlite3 import Error


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def main():
    sql_create_projects_table = """CREATE TABLE IF NOT EXISTS channels (
                                        guild text PRIMARY KEY,
                                        channel text
                                    ); 
                                    """

    sql_create_phrases_table = """CREATE TABLE IF NOT EXISTS phrases (
                                        guild text,
                                        phrase text,
                                        CONSTRAINT pkey PRIMARY KEY (guild, phrase)
                                    );"""

    sql_create_nicknames_table = """CREATE TABLE IF NOT EXISTS nicknames (
                                        account text PRIMARY KEY,
                                        nickname text
                                    );"""

    sql_create_disabled_table = """CREATE TABLE IF NOT EXISTS disabled (
                                        account text PRIMARY KEY
                                    );"""

    # create a database connection
    conn = create_connection()

    # create tables
    if conn is not None:
        # create projects table
        create_table(conn, sql_create_projects_table)
        create_table(conn, sql_create_phrases_table)
        create_table(conn, sql_create_nicknames_table)
        create_table(conn, sql_create_disabled_table)
    else:
        print("Error! cannot create the database connection.")


if __name__ == '__main__':
    main()
