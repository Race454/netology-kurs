CREATE TABLE исполнители (
    id INT PRIMARY KEY AUTO_INCREMENT,
    имя VARCHAR(100) NOT NULL
);

CREATE TABLE жанры (
    id INT PRIMARY KEY AUTO_INCREMENT,
    название VARCHAR(100) NOT NULL
);

CREATE TABLE альбомы (
    id INT PRIMARY KEY AUTO_INCREMENT,
    название VARCHAR(100) NOT NULL,
    год_выпуска INT NOT NULL
);

CREATE TABLE треки (
    id INT PRIMARY KEY AUTO_INCREMENT,
    название VARCHAR(100) NOT NULL,
    продолжительность TIME NOT NULL
);

CREATE TABLE сборники (
    id INT PRIMARY KEY AUTO_INCREMENT,
    название VARCHAR(100) NOT NULL,
    год_выпуска INT NOT NULL
);

CREATE TABLE исполнители_жанры (
    исполнитель_id INT,
    жанр_id INT,
    FOREIGN KEY (исполнитель_id) REFERENCES исполнители(id),
    FOREIGN KEY (жанр_id) REFERENCES жанры(id)
);

CREATE TABLE исполнители_альбомы (
    исполнитель_id INT,
    альбом_id INT,
    FOREIGN KEY (исполнитель_id) REFERENCES исполнители(id),
    FOREIGN KEY (альбом_id) REFERENCES альбомы(id)
);

CREATE TABLE сборники_треки (
    сборник_id INT,
    трек_id INT,
    FOREIGN KEY (сборник_id) REFERENCES сборники(id),
    FOREIGN KEY (трек_id) REFERENCES треки(id)
);

INSERT INTO исполнители (имя) VALUES 
('Исполнитель 1'),
('Исполнитель 2'),
('Исполнитель 3'),
('Исполнитель 4');

INSERT INTO жанры (название) VALUES 
('Жанр 1'),
('Жанр 2'),
('Жанр 3');

INSERT INTO альбомы (название, год_выпуска) VALUES 
('Альбом 1', 2019),
('Альбом 2', 2020),
('Альбом 3', 2021);

INSERT INTO треки (название, продолжительность) VALUES 
('Трек 1', '00:03:30'),
('Трек 2', '00:04:00'),
('Трек 3', '00:02:50'),
('Трек 4', '00:05:10'),
('Трек 5', '00:03:45'),
('Трек 6', '00:04:20');

INSERT INTO сборники (название, год_выпуска) VALUES 
('Сборник 1', 2018),
('Сборник 2', 2019),
('Сборник 3', 2020),
('Сборник 4', 2021);

INSERT INTO исполнители_жанры (исполнитель_id, жанр_id) VALUES 
(1, 1),
(2, 2),
(3, 3),
(4, 1),
(4, 2);

INSERT INTO исполнители_альбомы (исполнитель_id, альбом_id) VALUES 
(1, 1),
(2, 2),
(3, 3),
(4, 1);

INSERT INTO сборники_треки (сборник_id, трек_id) VALUES 
(1, 1),
(2, 2),
(3, 3),
(4, 4);