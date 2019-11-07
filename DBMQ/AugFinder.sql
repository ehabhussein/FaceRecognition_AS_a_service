-- phpMyAdmin SQL Dump
-- version 4.6.6deb5
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Aug 05, 2019 at 04:03 PM
-- Server version: 5.7.27-0ubuntu0.18.04.1
-- PHP Version: 7.2.19-0ubuntu0.18.04.1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `AugFinder`
--

-- --------------------------------------------------------

--
-- Table structure for table `Augface`
--

CREATE TABLE `Augface` (
  `id` int(11) NOT NULL,
  `StatusToken` varchar(255) DEFAULT NULL,
  `Priority` int(1) DEFAULT '0',
  `Age` int(3) DEFAULT NULL,
  `Status` int(1) DEFAULT '0',
  `Reported` tinyint(1) DEFAULT '0',
  `request_count` int(11) DEFAULT '0',
  `DateCreated` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `ModifiedTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `FaceToken` varchar(255) DEFAULT NULL,
  `gender` tinyint(1) DEFAULT NULL,
  `longitude` decimal(10,8) DEFAULT NULL,
  `latitude` decimal(11,8) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `Search`
--

CREATE TABLE `Search` (
  `id` int(11) NOT NULL,
  `age` int(11) DEFAULT NULL,
  `unmatched` longtext,
  `lat` decimal(10,8) NOT NULL,
  `lon` decimal(11,8) NOT NULL,
  `status` int(11) NOT NULL,
  `stoken` varchar(255) NOT NULL,
  `datecreated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `matched` longtext,
  `modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `flag` int(11) DEFAULT NULL,
  `searches` int(11) DEFAULT '0',
  `gender` tinyint(1) DEFAULT NULL,
  `synced` tinyint(1) DEFAULT '0',
  `searching` tinyint(1) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `search_trained_status`
--

CREATE TABLE `search_trained_status` (
  `id` int(11) NOT NULL,
  `search_id` int(11) NOT NULL,
  `trained_id` int(11) NOT NULL,
  `phase` int(11) NOT NULL,
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_match` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `Augface`
--
ALTER TABLE `Augface`
  ADD UNIQUE KEY `id` (`id`) USING BTREE,
  ADD UNIQUE KEY `id_3` (`id`),
  ADD UNIQUE KEY `Stok` (`StatusToken`) USING BTREE,
  ADD UNIQUE KEY `FaceToken` (`FaceToken`) USING BTREE,
  ADD UNIQUE KEY `id_2` (`id`,`FaceToken`),
  ADD UNIQUE KEY `StatusToken` (`StatusToken`),
  ADD KEY `Pri` (`Priority`) USING BTREE,
  ADD KEY `status` (`Status`) USING BTREE,
  ADD KEY `Age` (`Age`),
  ADD KEY `Reported` (`Reported`),
  ADD KEY `longitude` (`longitude`),
  ADD KEY `latitude` (`latitude`);

--
-- Indexes for table `Search`
--
ALTER TABLE `Search`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `stoken_2` (`stoken`),
  ADD KEY `lat` (`lat`),
  ADD KEY `lon` (`lon`),
  ADD KEY `stoken` (`stoken`);

--
-- Indexes for table `search_trained_status`
--
ALTER TABLE `search_trained_status`
  ADD PRIMARY KEY (`id`),
  ADD KEY `search_id` (`search_id`,`trained_id`,`phase`),
  ADD KEY `search_id_2` (`search_id`,`trained_id`,`phase`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `Augface`
--
ALTER TABLE `Augface`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
--
-- AUTO_INCREMENT for table `Search`
--
ALTER TABLE `Search`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `search_trained_status`
--
ALTER TABLE `search_trained_status`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
