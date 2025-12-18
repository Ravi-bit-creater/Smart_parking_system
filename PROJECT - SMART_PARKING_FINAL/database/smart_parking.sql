CREATE DATABASE smart_parking;
USE smart_parking;

CREATE TABLE user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(15),
    vehicle_number VARCHAR(20),
    password VARCHAR(100)
);

CREATE TABLE parking_area (
    area_id INT AUTO_INCREMENT PRIMARY KEY,
    area_name VARCHAR(100),
    total_slots INT,
    address VARCHAR(255)
);

INSERT INTO parking_area (area_name, total_slots, address)
VALUES
('Zone A – Ground Floor', 25, 'Main Building, Block A, Ground Floor'),
('Zone B – Basement', 30, 'Main Building, Block B, Basement Parking'),
('Zone C – Open Parking', 40, 'Near Main Gate, Open Parking Space'),
('Zone D – VIP Parking', 10, 'Admin Block, Near Reception Entrance');


select * from parking_area;

CREATE TABLE parking_slot (
    slot_id INT AUTO_INCREMENT PRIMARY KEY,
    slot_number VARCHAR(10),
    slot_type VARCHAR(20),
    availability VARCHAR(20),
    area_id INT,
    status ENUM('available', 'occupied') DEFAULT 'available',
    FOREIGN KEY (area_id) REFERENCES parking_area(area_id)
);

ALTER TABLE parking_slot
ADD COLUMN status ENUM('available', 'occupied') DEFAULT 'available';

ALTER TABLE parking_slot
ADD COLUMN vehicle_number VARCHAR(50) NULL;

ALTER TABLE parking_slot
ADD vehicle_type VARCHAR(20);

ALTER TABLE parking_slot ADD COLUMN booking_time DATETIME NULL;

ALTER TABLE parking_slot 
ADD COLUMN checkout_time DATETIME NULL,
ADD COLUMN parking_fee INT NULL;


INSERT INTO parking_slot (slot_number, slot_type, availability, area_id, status)
VALUES
('A1', 'Car', 'Yes', 1, 'available'),
('A2', 'Car', 'No', 1, 'occupied'),
('B1', 'Car', 'Yes', 2, 'available'),
('B2', 'Bike', 'No', 2, 'occupied'),
('C1', 'Car', 'Yes', 3, 'available'),
('D1', 'Car', 'No', 4, 'occupied');

INSERT INTO parking_slot (slot_number, slot_type, status, area_id)
VALUES
-- Zone A (25 slots)
('A3', 'Car', 'available', 1), ('A4', 'Car', 'available', 1), ('A5', 'Car', 'available', 1),
('A6', 'Car', 'available', 1), ('A7', 'Car', 'available', 1), ('A8', 'Car', 'available', 1), ('A9', 'Car', 'available', 1), ('A10', 'Car', 'available', 1),
('A11', 'Car', 'available', 1), ('A12', 'Car', 'available', 1), ('A13', 'Car', 'available', 1), ('A14', 'Car', 'available', 1), ('A15', 'Car', 'available', 1),
('A16', 'Car', 'available', 1), ('A17', 'Car', 'available', 1), ('A18', 'Car', 'available', 1), ('A19', 'Car', 'available', 1), ('A20', 'Car', 'available', 1),
('A21', 'Car', 'available', 1), ('A22', 'Car', 'available', 1), ('A23', 'Car', 'available', 1), ('A24', 'Car', 'available', 1), ('A25', 'Car', 'available', 1),

-- Zone B (30 slots)
('B3', 'Car', 'available', 2), ('B4', 'Car', 'available', 2), ('B5', 'Car', 'available', 2),
('B6', 'Car', 'available', 2), ('B7', 'Car', 'available', 2), ('B8', 'Car', 'available', 2), ('B9', 'Car', 'available', 2), ('B10', 'Car', 'available', 2),
('B11', 'Car', 'available', 2), ('B12', 'Car', 'available', 2), ('B13', 'Car', 'available', 2), ('B14', 'Car', 'available', 2), ('B15', 'Car', 'available', 2),
('B16', 'Car', 'available', 2), ('B17', 'Car', 'available', 2), ('B18', 'Car', 'available', 2), ('B19', 'Car', 'available', 2), ('B20', 'Car', 'available', 2),
('B21', 'Car', 'available', 2), ('B22', 'Car', 'available', 2), ('B23', 'Car', 'available', 2), ('B24', 'Car', 'available', 2), ('B25', 'Car', 'available', 2),
('B26', 'Car', 'available', 2), ('B27', 'Car', 'available', 2), ('B28', 'Car', 'available', 2), ('B29', 'Car', 'available', 2), ('B30', 'Car', 'available', 2),

-- Zone C (40 slots)
('C2', 'Car', 'available', 3), ('C3', 'Car', 'available', 3), ('C4', 'Car', 'available', 3), ('C5', 'Car', 'available', 3),
('C6', 'Car', 'available', 3), ('C7', 'Car', 'available', 3), ('C8', 'Car', 'available', 3), ('C9', 'Car', 'available', 3), ('C10', 'Car', 'available', 3),
('C11', 'Car', 'available', 3), ('C12', 'Car', 'available', 3), ('C13', 'Car', 'available', 3), ('C14', 'Car', 'available', 3), ('C15', 'Car', 'available', 3),
('C16', 'Car', 'available', 3), ('C17', 'Car', 'available', 3), ('C18', 'Car', 'available', 3), ('C19', 'Car', 'available', 3), ('C20', 'Car', 'available', 3),
('C21', 'Car', 'available', 3), ('C22', 'Car', 'available', 3), ('C23', 'Car', 'available', 3), ('C24', 'Car', 'available', 3), ('C25', 'Car', 'available', 3),
('C26', 'Car', 'available', 3), ('C27', 'Car', 'available', 3), ('C28', 'Car', 'available', 3), ('C29', 'Car', 'available', 3), ('C30', 'Car', 'available', 3),
('C31', 'Car', 'available', 3), ('C32', 'Car', 'available', 3), ('C33', 'Car', 'available', 3), ('C34', 'Car', 'available', 3), ('C35', 'Car', 'available', 3),
('C36', 'Car', 'available', 3), ('C37', 'Car', 'available', 3), ('C38', 'Car', 'available', 3), ('C39', 'Car', 'available', 3), ('C40', 'Car', 'available', 3),

-- Zone D (10 slots)
('D2', 'Car', 'available', 4), ('D3', 'Car', 'available', 4), ('D4', 'Car', 'available', 4), ('D5', 'Car', 'available', 4),
('D6', 'Car', 'available', 4), ('D7', 'Car', 'available', 4), ('D8', 'Car', 'available', 4), ('D9', 'Car', 'available', 4), ('D10', 'Car', 'available', 4);

select slot_id, slot_number,area_id from parking_slot where area_id = 2;

select * from parking_slot;
SELECT slot_id, slot_number, slot_type, status, 
vehicle_number, vehicle_type, booking_time FROM parking_slot;

UPDATE parking_slot
SET area_id = 4
WHERE slot_id = 6;

CREATE TABLE booking (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    slot_id INT,
    booking_date DATE,
    in_time DATETIME,
    out_time DATETIME,
    status VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES user(user_id),
    FOREIGN KEY (slot_id) REFERENCES parking_slot(slot_id)
);

select * from booking;

UPDATE parking_slot SET area_id = 1 WHERE slot_id BETWEEN 1 AND 25;
UPDATE parking_slot SET area_id = 2 WHERE slot_id BETWEEN 26 AND 55;

select * from parking_slot;

DESCRIBE parking_area;
DESCRIBE parking_slot;

ALTER TABLE user ADD role VARCHAR(20) DEFAULT 'user';

select * from user;

delete from user where user_id = 2;

update user set role = 'admin' where user_id = 3;