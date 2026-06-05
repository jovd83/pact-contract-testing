package com.example;

/** Minimal view of a Pet — only the fields this consumer actually uses. */
public record Pet(int id, String name, String status) {}
