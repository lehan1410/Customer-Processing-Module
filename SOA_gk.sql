-- Tạo database nếu chưa có
CREATE DATABASE IF NOT EXISTS Order_Services;
USE Order_Services;

-- Tạo bảng Package

CREATE TABLE Package (
    package_id INT PRIMARY KEY,
    package_name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL
);

INSERT INTO Package (package_id, package_name, description, price) VALUES
(1, 'Buffet 199k', 'Bao gồm các món ăn nhanh hấp dẫn như burger bò nướng sốt đặc biệt, khoai tây chiên giòn và nước ngọt không giới hạn.', 199000),
(2, 'Buffet 299k', 'Gồm pizza hải sản tươi ngon, mì ý sốt bò bằm và salad rau trộn.', 299000),
(3, 'Buffet 399k', 'Thực đơn đặc biệt gồm gà rán giòn cay, sushi cá hồi, hải sản tươi sống và món tráng miệng hấp dẫn', 399000),
(4, 'A-la-carte', 'Các món ăn gọi riêng lẻ', 0),
(5, 'Combo 01: Gà rán, Cánh gà chiên nước mắm', 'Gồm 2 miếng gà rán giòn rụm, khoai tây chiên vàng giòn và 1 Cánh gà chiên nước mắm.', 99000),
(6, 'Combo 02: Mì Ý sốt bò bằm, Trà đào cam sả', 'Một phần mì Spaghetti sốt bò bằm đậm đà, đi kèm một ly trà đào cam sả.', 80000),
(7, 'Combo 03: Sushi đặc biệt, Kem chocolate', 'Gồm 8 miếng sushi cá hồi, cá ngừ và tôm tươi, ăn kèm nước tương, wasabi và gừng ngâm + Kem chocolate', 159000);

-- Menu
CREATE TABLE Menu (
    food_id INT PRIMARY KEY,
    food_name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    info TEXT,
    img_url VARCHAR(255),
    status INT DEFAULT 1
);

INSERT INTO Menu (food_id, food_name, price, info, img_url, status) VALUES
(1, 'Burger bò nướng sốt đặc biệt', 50000, 'Burger bò nướng với sốt đặc biệt', '', 1),
(2, 'Pokemon hải sản', 120000, 'Pokemon hải sản tươi ngon', '', 1),
(3, 'Pokemon thịt nguội', 100000, 'Pokemon phủ thịt nguội và phô mai mozzarella kéo sợi', '', 1),
(4, 'Gà rán giòn cay', 60000, 'Gà rán giòn cay', '', 1),
(5, 'Lẩu Thái hải sản', 200000, 'Lẩu Thái chua cay với hải sản tươi sống', '', 1),
(6, 'Gà rán giòn rụm', 30000, '2 miếng gà rán giòn rụm', '', 1),
(7, 'Cánh gà chiên nước mắm', 40000, 'Cánh gà chiên giòn phủ sốt nước mắm tỏi', '', 1),
(8, 'Mì Spaghetti sốt bò bằm', 50000, 'Mì Ý sốt cà chua bò bằm', '', 1),
(9, 'Trà đào cam sả', 25000, 'Trà đào mát lạnh pha cùng cam tươi và sả', '', 1),
(10, 'Sushi đặc biệt', 120000, '8 miếng sushi cá hồi, cá ngừ và tôm tươi', '', 1),
(11, 'Kem chocolate', 30000, 'Kem chocolate cao cấp với vị socola đậm đà', '', 1),
(12, 'Bánh mì bơ tỏi', 35000, 'Bánh mì bơ tỏi thơm giòn, ăn kèm rau thơm', '', 1),
(13, 'Soup bí đỏ', 40000, 'Soup bí đỏ kem tươi mịn màng, ăn kèm bánh mì nướng giòn', '', 1),
(14, 'Steak bò sốt tiêu', 150000, 'Steak bò Mỹ mềm mọng nước với sốt tiêu đen đặc biệt', '', 1),
(15, 'Bún bò Huế', 55000, 'Bún bò Huế truyền thống với nước dùng đậm đà và thịt bò thái mỏng', '', 1),
(16, 'Gỏi cuốn tôm thịt', 45000, 'Gỏi cuốn thanh mát với tôm sú, thịt heo luộc và rau sống', '', 1),
(17, 'Bánh cheesecake dâu', 45000, 'Bánh cheesecake mềm mịn với lớp dâu tươi bên trên', '', 1),
(18, 'Bánh mì bơ tỏi', 35000, 'Bánh mì bơ tỏi thơm giòn, ăn kèm rau thơm', '', 1),
(19, 'Soup bí đỏ', 40000, 'Soup bí đỏ kem tươi mịn màng, ăn kèm bánh mì nướng giòn', '', 1),
(20, 'Steak bò sốt tiêu', 150000, 'Steak bò Mỹ mềm mọng nước với sốt tiêu đen đặc biệt', '', 1),
(21, 'Bún bò Huế', 55000, 'Bún bò Huế truyền thống với nước dùng đậm đà và thịt bò thái mỏng', '', 1),
(22, 'Gỏi cuốn tôm thịt', 45000, 'Gỏi cuốn thanh mát với tôm sú, thịt heo luộc và rau sống', '', 1);

-- Package_Menu
CREATE TABLE Package_Menu (
    package_id INT,
    food_id INT,
    PRIMARY KEY (package_id, food_id),
    FOREIGN KEY (package_id) REFERENCES Package(package_id) ON DELETE CASCADE,
    FOREIGN KEY (food_id) REFERENCES Menu(food_id) ON DELETE CASCADE
);
INSERT INTO Package_Menu (package_id, food_id) VALUES
-- Buffet 199k (package_id = 1)
(1, 1),  -- Burger bò nướng sốt đặc biệt
(1, 6),  -- Gà rán giòn rụm
(1, 9),  -- Trà đào cam sả

-- Buffet 299k (package_id = 2): Bao gồm Buffet 199k + 3 món mới
(2, 1),  -- Burger bò nướng sốt đặc biệt
(2, 6),  -- Gà rán giòn rụm
(2, 9),  -- Trà đào cam sả
(2, 2),  -- Pizza hải sản
(2, 3),  -- Pizza thịt nguội
(2, 8),  -- Mì Spaghetti sốt bò bằm

-- Buffet 399k (package_id = 3): Bao gồm Buffet 299k + 3 món mới
(3, 1),  -- Burger bò nướng sốt đặc biệt
(3, 6),  -- Gà rán giòn rụm
(3, 9),  -- Trà đào cam sả
(3, 2),  -- Pizza hải sản
(3, 3),  -- Pizza thịt nguội
(3, 8),  -- Mì Spaghetti sốt bò bằm
(3, 4),  -- Gà rán giòn cay
(3, 5),  -- Lẩu Thái hải sản
(3, 10), -- Sushi đặc biệt

-- Combo 01 (package_id = 5)
(5, 6),  -- Gà rán giòn rụm
(5, 7),  -- Cánh gà chiên nước mắm

-- Combo 02 (package_id = 6)
(6, 8),  -- Mì Spaghetti sốt bò bằm
(6, 9),  -- Trà đào cam sả

-- Combo 03 (package_id = 7)
(7, 10), -- Sushi đặc biệt
(7, 11), -- Kem chocolate

-- A-la-carte (package_id = 4): Bao gồm tất cả món trong Menu
(4, 1),  (4, 2),  (4, 3),  (4, 4),
(4, 5),  (4, 6),  (4, 7),  (4, 8),
(4, 9),  (4, 10), (4, 11), (4, 12),
(4, 13), (4, 14), (4, 15), (4, 16),
(4, 17), (4, 18), (4, 19), (4, 20),
(4, 21), (4, 22);


-- Tạo bảng Tables
CREATE TABLE Tables (
    table_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    table_name VARCHAR(10) NOT NULL UNIQUE,
    status bit NOT NULL default 0
);

-- Tạo bảng Orders
CREATE TABLE Orders (
    order_id VARCHAR(10) NOT NULL PRIMARY KEY,
    table_id INT, 
    package_id VARCHAR(20),
    user_id VARCHAR(10) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    FOREIGN KEY (table_id) REFERENCES Tables(table_id) ON DELETE CASCADE
);

-- Tạo bảng Order_Items
CREATE TABLE Order_Items (
    order_item_id VARCHAR(10) NOT NULL PRIMARY KEY,
    order_id VARCHAR(10) NOT NULL,
    food_id VARCHAR(10) NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
);

-- Chèn dữ liệu vào bảng Tables (ID tự động tăng)
INSERT INTO Tables (table_name) VALUES 
('01'), ('02'), ('03'), ('04'), ('05'), ('06'), ('07'), ('08'), ('09'), ('10'),
('11'), ('12'), ('13'), ('14'), ('15');

create database Payment_Services
use Payment_Services


CREATE TABLE Invoices
(
  invoice_id VARCHAR(10) NOT NULL,
  order_id VARCHAR(10) NOT NULL,
  table_id INT NOT NULL,
  total_amount DECIMAL(10, 2) NOT NULL,
  issued_at datetime NOT NULL,
  PRIMARY KEY (invoice_id),
);

CREATE TABLE Payments 
(
  payment_id VARCHAR(10) NOT NULL,
  invoice_id VARCHAR(10) NOT NULL,
  payment_method VARCHAR(20) NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  paid_at datetime NOT NULL,
  status bit NOT NULL default 0,
  FOREIGN KEY (invoice_id) REFERENCES Invoices(invoice_id) ON DELETE CASCADE,
  PRIMARY KEY (payment_id),
);

create database User_Services
use User_Services

CREATE TABLE Users
(
  user_id VARCHAR(10) NOT NULL,
  user_name VARCHAR(20) NOT NULL,
  password VARCHAR(20) NOT NULL,
  role_id VARCHAR(10) NOT NULL,
  PRIMARY KEY (user_id)
);

CREATE TABLE User_Profile
(
  name VARCHAR(50) NOT NULL,
  DOB DATE NOT NULL,
  Address VARCHAR(50) NOT NULL,
  Email VARCHAR(50) NOT NULL,
  role VARCHAR(50) NOT NULL,
  user_id VARCHAR(10) NOT NULL,
  FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

INSERT INTO Users (user_id, user_name, password, role_id) VALUES
('U001', 'admin_1', '123', 'A001'),
('U002', 'chef_1', '123', 'C001'),
('U003', 'waiter_1', '123', 'W001'),
('U004', 'admin_2', '123', 'A002'),
('U005', 'chef_2', '123', 'C002'),
('U006', 'waiter_2', '123', 'W002');

INSERT INTO User_Profile (name, DOB, Address, Email, role, user_id) VALUES
('John Doe', '1990-05-15', '123 Main St', 'johndoe@example.com', 'Admin', 'U001'),
('Sarah Connor', '1985-09-21', '456 Oak Ave', 'sarah@example.com', 'Chef', 'U002'),
('David Smith', '1993-07-12', '789 Pine Blvd', 'david@example.com', 'Waiter', 'U003'),
('Alice Johnson', '1995-12-03', '101 Maple Rd', 'alice@example.com', 'Admin', 'U004'),
('Bob Martin', '2000-03-27', '202 Cedar Ln', 'bob@example.com', 'Chef','U005'),
('Jack', '2000-05-30', '202 Cedar Ln', 'bob@example.com', 'Waiter', 'U006');

