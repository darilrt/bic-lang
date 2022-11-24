#pragma once
#include "iostream"
enum class TokenType {
    EndOfFile,
    Ident,
    Int,
    Float,
    String,
    True,
    False,
    Null,
    Add,
    Sub,
    Mul,
    Div,
    Mod,
};
class Token {
public: TokenType m_type;
public: std::string m_literal;
public: Token(TokenType t, const std::string& literal);
};

