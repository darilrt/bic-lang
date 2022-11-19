#include <cstdio>
#include <cstring>
class String {
    public: char* m_data;
    private: int m_size;
    public: [[nodiscard]]  String() {
        m_data = 0;
        m_size = 0;
    };
    public: [[nodiscard]]  String(const char* data) {
        this->m_size = strlen(data);
        this->m_data = new char[this->m_size + 1];
        this->m_data[this->m_size] = 0;
        memcpy(this->m_data, data, this->m_size);
    };
    public: [[nodiscard]] int Size() const {
        return this->m_size;
    };
};
void print(char* str) {
    printf("%s", str);
};
void print(const String& str) {
    printf("%s", str.m_data);
};
void print(int val) {
    printf("%d", val);
};
void print(float val) {
    printf("%f", val);
};
void print(double val) {
    printf("%f", val);
};
void print(bool val) {
    if (val) {
        printf("true");
    } else {
        printf("false");
    };
};
void print(char val) {
    printf("%c", val);
};
template <typename T> void print(const T& o) {
    printf(o);
};
template <typename E, typename... T> void print(const E& o, const T&... args) {
    print(o);
    print(args...);
};
[[nodiscard]] int main() {
    String s = String("Hello, ");
    print(s, "World!");
    return 0;
};