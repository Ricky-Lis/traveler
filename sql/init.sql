-- ============================================
-- Travel App 数据库初始化脚本
-- MySQL 8.0+
-- ============================================

CREATE DATABASE IF NOT EXISTS `travel`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `travel`;

-- 按外键依赖倒序删除
DROP TABLE IF EXISTS `travel_view_log`;
DROP TABLE IF EXISTS `travel_city`;
DROP TABLE IF EXISTS `footprint_image`;
DROP TABLE IF EXISTS `footprint`;
DROP TABLE IF EXISTS `city`;
DROP TABLE IF EXISTS `travel`;
DROP TABLE IF EXISTS `user`;

-- ============================================
-- 1. 用户表
-- ============================================
CREATE TABLE `user` (
    `id`             BIGINT       NOT NULL AUTO_INCREMENT,
    `nickname`       VARCHAR(50)  NOT NULL DEFAULT '' COMMENT '昵称',
    `avatar`         VARCHAR(255) NOT NULL DEFAULT '' COMMENT '头像 URL',
    `email`          VARCHAR(100) NOT NULL COMMENT '登录邮箱',
    `password_hash`  VARCHAR(255) NOT NULL COMMENT '密码哈希',
    `bio`            VARCHAR(255) NOT NULL DEFAULT '' COMMENT '个人简介',
    `is_active`      TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否启用 0-禁用 1-启用',
    `email_verified` TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '邮箱是否已验证 0-否 1-是',
    `last_login_at`  DATETIME     DEFAULT NULL COMMENT '最后登录时间',
    `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- 2. 旅程表
-- ============================================
CREATE TABLE `travel` (
    `id`              BIGINT        NOT NULL AUTO_INCREMENT,
    `user_id`         BIGINT        NOT NULL COMMENT '所属用户',
    `title`           VARCHAR(100)  NOT NULL COMMENT '旅程标题',
    `description`     TEXT          DEFAULT NULL COMMENT '旅程描述',
    `cover_image_url` VARCHAR(500)  NOT NULL DEFAULT '' COMMENT '封面图 URL（OSS）',
    `start_date`      DATE          DEFAULT NULL COMMENT '出发日期',
    `end_date`        DATE          DEFAULT NULL COMMENT '结束日期',
    `status`          TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '旅程状态 0-草稿 1-进行中 2-已完成',
    `is_public`       TINYINT(1)    NOT NULL DEFAULT 1 COMMENT '是否公开 0-私密 1-公开',
    `view_count`      INT UNSIGNED  NOT NULL DEFAULT 0 COMMENT '浏览量',
    `footprint_count` INT UNSIGNED  NOT NULL DEFAULT 0 COMMENT '足迹数（冗余计数）',
    `image_count`     INT UNSIGNED  NOT NULL DEFAULT 0 COMMENT '图片总数（冗余计数）',
    `created_at`      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_travel_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
    INDEX `idx_travel_user_id` (`user_id`),
    INDEX `idx_travel_status` (`status`),
    INDEX `idx_travel_is_public` (`is_public`),
    INDEX `idx_travel_start_date` (`start_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='旅程表';

-- ============================================
-- 3. 足迹表
-- ============================================
CREATE TABLE `footprint` (
    `id`                  BIGINT         NOT NULL AUTO_INCREMENT,
    `travel_id`           BIGINT         NOT NULL COMMENT '所属旅程',
    `user_id`             BIGINT         NOT NULL COMMENT '所属用户',

    -- 地理信息（逆地理编码结果，支持用户手动调整）
    `latitude`            DECIMAL(10,7)  NOT NULL COMMENT '纬度',
    `longitude`           DECIMAL(10,7)  NOT NULL COMMENT '经度',
    `location_name`       VARCHAR(255)   NOT NULL DEFAULT '' COMMENT '地点名称（景点/POI）',
    `address`             VARCHAR(500)   NOT NULL DEFAULT '' COMMENT '详细地址（逆地理编码）',
    `district`            VARCHAR(100)   NOT NULL DEFAULT '' COMMENT '区县',
    `city_name`           VARCHAR(100)   NOT NULL DEFAULT '' COMMENT '城市名称',
    `province_name`       VARCHAR(100)   NOT NULL DEFAULT '' COMMENT '省份名称',
    `country_name`        VARCHAR(100)   NOT NULL DEFAULT '' COMMENT '国家名称',
    `location_adjusted`   TINYINT(1)     NOT NULL DEFAULT 0 COMMENT '是否手动调整过位置 0-否 1-是',

    -- 内容
    `description`         TEXT           DEFAULT NULL COMMENT '足迹描述',
    `cover_thumbnail_url` VARCHAR(500)   NOT NULL DEFAULT '' COMMENT '封面缩略图 URL（首图，供地图 Marker 直出）',
    `image_count`         INT UNSIGNED   NOT NULL DEFAULT 0 COMMENT '图片数（冗余计数）',

    -- 排序 & 时间
    `travel_time`         DATETIME       DEFAULT NULL COMMENT '到达时间（用户可调整，用于路线串联）',
    `sort_order`          INT            NOT NULL DEFAULT 0 COMMENT '手动排序权重（可拖动）',

    `created_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_footprint_travel` FOREIGN KEY (`travel_id`) REFERENCES `travel` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_footprint_user`   FOREIGN KEY (`user_id`)   REFERENCES `user` (`id`)   ON DELETE CASCADE,
    INDEX `idx_fp_travel_id` (`travel_id`),
    INDEX `idx_fp_user_id` (`user_id`),
    INDEX `idx_fp_travel_time` (`travel_time`),
    INDEX `idx_fp_sort_order` (`travel_id`, `sort_order`),
    INDEX `idx_fp_lat_lng` (`latitude`, `longitude`),
    INDEX `idx_fp_city` (`city_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='足迹表';

-- ============================================
-- 4. 足迹图片表
-- ============================================
CREATE TABLE `footprint_image` (
    `id`            BIGINT        NOT NULL AUTO_INCREMENT,
    `footprint_id`  BIGINT        NOT NULL COMMENT '所属足迹',
    `original_url`  VARCHAR(500)  NOT NULL COMMENT '原图 URL（OSS）',
    `thumbnail_url` VARCHAR(500)  NOT NULL COMMENT '缩略图 URL（OSS）',
    `width`         INT UNSIGNED  DEFAULT NULL COMMENT '原图宽度 px',
    `height`        INT UNSIGNED  DEFAULT NULL COMMENT '原图高度 px',
    `size_kb`       INT UNSIGNED  DEFAULT NULL COMMENT '原图大小 KB',
    `sort_order`    INT           NOT NULL DEFAULT 0 COMMENT '图片排序',
    `created_at`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_fpimg_footprint` FOREIGN KEY (`footprint_id`) REFERENCES `footprint` (`id`) ON DELETE CASCADE,
    INDEX `idx_fpimg_footprint_id` (`footprint_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='足迹图片表';

-- ============================================
-- 5. 城市表
-- ============================================
CREATE TABLE `city` (
    `id`        BIGINT         NOT NULL AUTO_INCREMENT,
    `name`      VARCHAR(100)   NOT NULL COMMENT '城市名称',
    `province`  VARCHAR(100)   NOT NULL DEFAULT '' COMMENT '省份/州',
    `country`   VARCHAR(100)   NOT NULL DEFAULT '' COMMENT '国家',
    `latitude`  DECIMAL(10,7)  DEFAULT NULL COMMENT '城市中心纬度',
    `longitude` DECIMAL(10,7)  DEFAULT NULL COMMENT '城市中心经度',
    `created_at` DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_city` (`country`, `province`, `name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='城市表';

-- ============================================
-- 6. 旅程-城市关联表（多对多）
-- ============================================
CREATE TABLE `travel_city` (
    `id`        BIGINT   NOT NULL AUTO_INCREMENT,
    `travel_id` BIGINT   NOT NULL COMMENT '旅程 ID',
    `city_id`   BIGINT   NOT NULL COMMENT '城市 ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_tc_travel` FOREIGN KEY (`travel_id`) REFERENCES `travel` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_tc_city`   FOREIGN KEY (`city_id`)   REFERENCES `city` (`id`)   ON DELETE CASCADE,
    UNIQUE KEY `uk_travel_city` (`travel_id`, `city_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='旅程-城市关联表';

-- ============================================
-- 7. 旅程浏览日志（宽松约束，保障写入性能）
-- ============================================
CREATE TABLE `travel_view_log` (
    `id`         BIGINT      NOT NULL AUTO_INCREMENT,
    `travel_id`  BIGINT      NOT NULL COMMENT '旅程 ID',
    `user_id`    BIGINT      DEFAULT NULL COMMENT '浏览用户（匿名为 NULL）',
    `ip_address` VARCHAR(50) NOT NULL DEFAULT '' COMMENT '访客 IP',
    `user_agent` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '浏览器 UA',
    `created_at` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '浏览时间',
    PRIMARY KEY (`id`),
    INDEX `idx_vlog_travel_id` (`travel_id`),
    INDEX `idx_vlog_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='旅程浏览日志表';
