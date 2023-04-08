CREATE TABLE IF NOT EXISTS ArcanVersion (
    id int NOT NULL AUTO_INCREMENT,
    date_of_release timestamp,
    version varchar(255) UNIQUE,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS Repository (
    id int NOT NULL AUTO_INCREMENT,
    project_repository varchar(255),
    branch varchar(255),
    username varchar(255),
    password varchar(255),
    PRIMARY KEY (id) 
);

CREATE TABLE IF NOT EXISTS Project (
    id int NOT NULL AUTO_INCREMENT,
    id_repository int UNIQUE,
    language varchar(255),
    name varchar(255),
    PRIMARY KEY (id),
    FOREIGN KEY (id_repository) REFERENCES Repository(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Version (
    id int NOT NULL AUTO_INCREMENT,
    id_commit varchar(255),
    date_commit timestamp,
    id_project int,
    PRIMARY KEY (id),
    FOREIGN KEY (id_project) REFERENCES Project(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS DependencyGraph (
    id int NOT NULL AUTO_INCREMENT,
    date_parsing timestamp,
    file_result blob,
    project_version int,
    PRIMARY KEY (id),
    FOREIGN KEY (project_version) REFERENCES Version(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Analysis (
    id int NOT NULL AUTO_INCREMENT,
    date_analysis timestamp,
    file_result blob,
    project_version int,
    arcan_version int,
    PRIMARY KEY (id),
    FOREIGN KEY (project_version) REFERENCES Version(id) ON DELETE CASCADE,
    FOREIGN KEY (arcan_version) REFERENCES ArcanVersion(id) ON DELETE CASCADE
);