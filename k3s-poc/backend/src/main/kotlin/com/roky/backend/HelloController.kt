package com.roky.backend

import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RestController

@RestController
class HelloController {

	@GetMapping("/api/hello")
	fun getHelloMessage(): Map<String, String> = mapOf("message" to "Hello from k3s!")
}
