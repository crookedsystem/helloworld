package com.roky.backend.user

import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api/users")
class UserController(
	private val userRepository: UserRepository,
) {

	data class CreateUserRequest(val name: String)

	data class UserResponse(val id: Long?, val name: String)

	@PostMapping
	fun create(@RequestBody request: CreateUserRequest): UserResponse {
		val savedUser = userRepository.save(User(request.name))
		return UserResponse(savedUser.id, savedUser.name)
	}

	@GetMapping
	fun findAll(): List<UserResponse> {
		val users = userRepository.findAll()
		return users.map { UserResponse(it.id, it.name) }
	}
}
