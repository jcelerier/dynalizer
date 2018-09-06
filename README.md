# Dynalizer

A python script which generates a C++ dynamic loader for shared objects,
given a C header file. Useful when you don't want to link at compile-time,
and if you want to have a beginning of C++ API for your C code.

## Dependencies

`pip install clang inflection`

# Example

```
$ echo 'void mylib_foo(int x, const char* bar);\nvoid mylib_bar(float** z);' > mylib.h
$ python dynalizer.py header.h
```

will produce a class akin to the following :

```C++
class mylib
{
public:
  // Pass the path to your .so / .dll / .dylib here
  explicit mylib(const char* filepath)
    : m_lib{filepath}
  {
    m_sym_mylib_foo = m_lib.symbol<decltype(::mylib_foo)*>("mylib_foo");
    if(!m_sym_mylib_foo)
      throw std::runtime_error("Invalid symbol lookup: mylib_foo");

    m_sym_mylib_bar = m_lib.symbol<decltype(::mylib_bar)*>("mylib_bar");
    if(!m_sym_mylib_bar)
      throw std::runtime_error("Invalid symbol lookup: mylib_bar");
  }

  static auto& instance() {
    static mylib c;
    return c;
  }
  
  template<typename... Args>
  auto mylib_foo(Args&&... args) -> decltype(auto)
  {
    return m_sym_mylib_foo(std::forward<Args>(args)...);
  }

  template<typename... Args>
  auto mylib_bar(Args&&... args) -> decltype(auto)
  {
    return m_sym_mylib_bar(std::forward<Args>(args)...);
  }

private:
  decltype(::mylib_foo)* m_sym_mylib_foo{};
  decltype(::mylib_bar)* m_sym_mylib_bar{};

  dynalizer::library m_lib;
};

```

# Options

Multiple codegen aspects can be changed:

* Lazy (`--lazy`) and eager (`--eager`) loading: in the eager case,
  all the symbols are loaded upon instantiation of the library.
  In the lazy case, symbols are not loaded until they are actually used.

* Error reporting : `--throw` and `--abort`. These options define what happens
  when a symbol is missing: an exception, or an assertion.

* Prettification : `--pretty`. If possible, will remove common suffixes of the API
  functions, and will port to standard C++ `snake_case`.

  That is, the earlier example would become instead:

```C++
template<typename... Args>
auto foo(Args&&... args) -> decltype(auto)
{
  return m_sym_mylib_foo(std::forward<Args>(args)...);
}

template<typename... Args>
auto bar(Args&&... args) -> decltype(auto)
{
  return m_sym_mylib_bar(std::forward<Args>(args)...);
}
```

so that usage patterns can be akin to :

```C++
int main() {
  auto& pa = portaudio::instance();
  pa.open_stream(...);
  pa.close_stream(...);
}
```

instead of the much heavier

```C++
int main() {
  auto& pa = portaudio::instance();
  pa.Pa_OpenStream(...);
  pa.Pa_CloseStream(...);
}
```
