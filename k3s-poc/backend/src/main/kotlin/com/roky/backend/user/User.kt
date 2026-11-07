package com.roky.backend.user

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.GeneratedValue
import jakarta.persistence.GenerationType
import jakarta.persistence.Id
import jakarta.persistence.Table

// 기존 SQL 실습의 users 테이블과 충돌하지 않도록 app_users를 사용한다.
@Entity
@Table(name = "app_users")
class User(
	@Column(nullable = false)
	val name: String,
) {
	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	val id: Long? = null
}
