-- MySQL dump 10.13  Distrib 8.4.11, for Linux (x86_64)
--
-- Host: localhost    Database: pizza
-- ------------------------------------------------------
-- Server version	8.4.11

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `menu_items`
--

DROP TABLE IF EXISTS `menu_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `menu_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(60) NOT NULL,
  `description` varchar(120) NOT NULL,
  `category` enum('pizza','sides') NOT NULL,
  `type` enum('veg','nonveg') NOT NULL DEFAULT 'veg',
  `price` decimal(10,2) NOT NULL,
  `tag` varchar(20) DEFAULT NULL,
  `available` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  CONSTRAINT `menu_items_chk_1` CHECK ((`price` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `menu_items`
--

LOCK TABLES `menu_items` WRITE;
/*!40000 ALTER TABLE `menu_items` DISABLE KEYS */;
INSERT INTO `menu_items` VALUES (1,'Margherita','San Marzano tomato, fresh mozzarella, basil','pizza','veg',299.00,NULL,1,'2026-11-17 09:58:00'),(2,'Farmhouse','Capsicum, onion, mushroom, sweet corn','pizza','veg',349.00,NULL,1,'2026-11-17 09:58:00'),(3,'Paneer Tikka','Tandoori paneer, onion, green chilli, mint drizzle','pizza','veg',399.00,'Bestseller',1,'2026-11-17 09:58:00'),(4,'Four Cheese','Mozzarella, cheddar, parmesan, gorgonzola','pizza','veg',429.00,NULL,1,'2026-11-17 09:58:00'),(5,'Pepperoni','Chicken pepperoni, mozzarella, oregano','pizza','nonveg',449.00,'Bestseller',1,'2026-11-17 09:58:00'),(6,'BBQ Chicken','Smoky BBQ sauce, grilled chicken, red onion','pizza','nonveg',469.00,NULL,1,'2026-11-17 09:58:00'),(7,'Chicken Keema','Spiced keema, jalapeño, coriander','pizza','nonveg',479.00,'Spicy',1,'2026-11-17 09:58:00'),(8,'Garlic Bread','Four pieces with herb butter','sides','veg',149.00,NULL,1,'2026-11-17 09:58:00'),(9,'Loaded Fries','Cheese sauce, peri-peri, spring onion','sides','veg',179.00,NULL,1,'2026-11-17 09:58:00'),(10,'Chocolate Lava Cake','Warm, with a molten centre','sides','veg',129.00,NULL,1,'2026-11-17 09:58:00'),(11,'Cold Drink (500 ml)','Coke, Sprite or Fanta','sides','veg',60.00,NULL,1,'2026-11-17 09:58:00'),(12,'Tiramisu','Back tomorrow','sides','veg',159.00,NULL,0,'2026-11-17 09:58:00');
/*!40000 ALTER TABLE `menu_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `phone` varchar(30) DEFAULT NULL,
  `email` varchar(254) NOT NULL,
  `message` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages`
--

LOCK TABLES `messages` WRITE;
/*!40000 ALTER TABLE `messages` DISABLE KEYS */;
INSERT INTO `messages` VALUES (1,'demo','9988776655','demo@demo.com','demo message','2026-11-05 17:32:40'),(2,'demo','9988776655','demo@demo.com','demo message','2026-11-05 17:33:20');
/*!40000 ALTER TABLE `messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_items`
--

DROP TABLE IF EXISTS `order_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `menu_item_id` int DEFAULT NULL,
  `item_name` varchar(255) NOT NULL,
  `quantity` int NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `order_id` (`order_id`),
  KEY `menu_item_id` (`menu_item_id`),
  CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`menu_item_id`) REFERENCES `menu_items` (`id`) ON DELETE SET NULL,
  CONSTRAINT `order_items_chk_1` CHECK ((`quantity` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_items`
--

LOCK TABLES `order_items` WRITE;
/*!40000 ALTER TABLE `order_items` DISABLE KEYS */;
INSERT INTO `order_items` VALUES (1,3,3,'Paneer Tikka',2,399.00),(2,3,8,'Garlic Bread',1,149.00),(3,4,1,'Margherita',2,299.00),(4,4,2,'Farmhouse',1,349.00);
/*!40000 ALTER TABLE `order_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_status_history`
--

DROP TABLE IF EXISTS `order_status_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_status_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `status` varchar(30) NOT NULL,
  `note` varchar(255) DEFAULT NULL,
  `changed_by` int DEFAULT NULL,
  `changed_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `order_id` (`order_id`),
  KEY `changed_by` (`changed_by`),
  CONSTRAINT `order_status_history_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `order_status_history_ibfk_2` FOREIGN KEY (`changed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_status_history`
--

LOCK TABLES `order_status_history` WRITE;
/*!40000 ALTER TABLE `order_status_history` DISABLE KEYS */;
INSERT INTO `order_status_history` VALUES (1,3,'Pending approval','Order placed',1,'2026-11-11 17:01:57'),(2,4,'Pending approval','Placed by the customer',3,'2026-11-17 09:59:04'),(3,4,'Accepted',NULL,2,'2026-11-17 09:59:05'),(4,4,'Preparing',NULL,2,'2026-11-17 09:59:05'),(5,4,'Out for delivery',NULL,2,'2026-11-17 09:59:05'),(6,4,'Delivered',NULL,2,'2026-11-17 09:59:05'),(7,3,'Rejected','Delivery area not covered',2,'2026-11-17 09:59:05');
/*!40000 ALTER TABLE `order_status_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_number` varchar(50) NOT NULL,
  `user_id` int NOT NULL,
  `customer_name` varchar(100) NOT NULL,
  `phone` varchar(15) NOT NULL,
  `address` varchar(255) NOT NULL,
  `landmark` varchar(100) DEFAULT NULL,
  `notes` varchar(255) DEFAULT NULL,
  `payment_method` varchar(30) NOT NULL DEFAULT 'Cash on delivery',
  `order_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('Pending approval','Accepted','Preparing','Out for delivery','Delivered','Rejected','Cancelled') NOT NULL DEFAULT 'Pending approval',
  `reject_reason` varchar(255) DEFAULT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `order_number` (`order_number`),
  KEY `user_id` (`user_id`),
  KEY `status` (`status`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` VALUES (3,'1049',1,'demo','9856547520','123,some street,some city',NULL,NULL,'Cash on delivery','2026-11-11 20:41:00','Rejected','Delivery area not covered',947.00,'2026-11-11 17:01:57'),(4,'1050',3,'Verify Customer','9812345670','42 Test Road, Test City',NULL,NULL,'Cash on delivery','2026-11-17 15:29:04','Delivered',NULL,947.00,'2026-11-17 09:59:04');
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(15) NOT NULL,
  `address` varchar(100) NOT NULL,
  `password` varchar(100) NOT NULL,
  `role` varchar(20) NOT NULL,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `phone` (`phone`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'demo','demo@demo.com','9856547520','123,some street,some city','pbkdf2:sha256:1000000$VOZDSrKA$edb6406a0397c42c95361a46ff0e8fd47e494d42010750a46d7a5f511bcf7756','customer','2026-11-10 22:52:35'),(2,'admin','admin@demo.com','9123456789','somecity','pbkdf2:sha256:1000000$plQuMAz3$ae80762676024806c2264531ccaf328a52f0cbe4a49f4c792d755d69ed01417c','admin','2026-11-16 21:40:48'),(3,'Verify Customer','verify.customer@example.com','9812345670','42 Test Road, Test City','pbkdf2:sha256:1000000$D7DIXOlF$1136dbc19aea6368266fd30901043b8ab5c41080edfff6b740f48888cc82dadc','customer','2026-11-17 15:29:04');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed
