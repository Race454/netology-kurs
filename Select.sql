-- Задание 2.
SELECT название, продолжительность FROM треки ORDER BY продолжительность DESC LIMIT 1;

SELECT название FROM треки WHERE продолжительность >= '00:03:30';

SELECT название FROM сборники WHERE год_выпуска BETWEEN 2018 AND 2020;

SELECT имя FROM исполнители WHERE имя NOT LIKE '% %';

SELECT название FROM треки WHERE название LIKE '%мой%' OR название LIKE '%my%';

-- Задание 3.
SELECT ж.название AS Жанр, COUNT(e.id) AS Количество_исполнителей 
FROM жанры ж LEFT JOIN исполнители_жанры ej ON ж.id = ej.жанр_id 
LEFT JOIN исполнители e ON ej.исполнитель_id = e.id 
GROUP BY ж.название;

SELECT COUNT(t.id) AS Количество_трека 
FROM треки t JOIN исполнители_альбомы ea ON t.id = ea.альбом_id 
WHERE ea.год_выпуска BETWEEN '2019' AND '2020';

SELECT a.название AS Альбом, AVG(t.продолжительность) AS Средняя_продолжительность 
FROM альбомы a LEFT JOIN исполнители_альбомы ea ON a.id = ea.альбом_id 
LEFT JOIN треки t ON ea.альбом_id = t.id 
GROUP BY a.название;

SELECT e.имя FROM исполнители e LEFT JOIN исполнители_альбомы ea ON e.id = ea.исполнитель_id 
WHERE ea.год_выпуска != '2020' OR ea.год_выпуска IS NULL;

SELECT s.название FROM сборники s JOIN сборники_треки st ON s.id = st.сборник_id 
JOIN треки t ON st.трек_id = t.id JOIN исполнители_альбомы ea ON t.id = ea.альбом_id 
WHERE ea.исполнитель_id = <id конкретного исполнителя>;


-- Задане 4.
SELECT a.название FROM альбомы a JOIN исполнители_альбомы ea ON a.id = ea.альбом_id 
JOIN исполнители_жанры ej ON ea.исполнитель_id = ej.исполнитель_id 
GROUP BY a.id HAVING COUNT(DISTINCT ej.janr_id) >1;

SELECT t.название FROM треки t LEFT JOIN сборники_треки st ON t.id = st.trak_id WHERE st.trak_id IS NULL;

SELECT e.* FROM исполнители e JOIN исполняемые_treki et ON e.id = et.ispitel' WHERE et.trak IN (SELECT MIN(t.dlina_traka ) FROM treki t );