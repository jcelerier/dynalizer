#pragma once
#if __has_include(<dlfcn.h>)
#include <dlfcn.h>
#elif __has_include(<Windows.h>)
#include <Windows.h>
#endif

namespace dynalizer
{
class library
{
public:
  explicit library(const char* const so) noexcept
  {
#ifdef _WIN32
    impl = (void*) LoadLibraryA(so);
#else
    impl = dlopen(so, RTLD_LAZY|RTLD_LOCAL|RTLD_NODELETE);
#endif
  }

  library(const library&) noexcept = delete;
  library& operator=(const library&) noexcept = delete;
  library(library&& other)
  {
    impl = other.impl;
    other.impl = nullptr;
  }

  library& operator=(library&& other) noexcept
  {
    impl = other.impl;
    other.impl = nullptr;
    return *this;
  }

  auto error() const
  {
#ifdef _WIN32
    return {};
#else
    return dlerror();
#endif
  }

  ~library()
  {
    if(impl)
    {
#ifdef _WIN32
      FreeLibrary((HMODULE)impl);
#else
      dlclose(impl);
#endif
    }
  }

  template<typename T>
  T symbol(const char* const sym) const noexcept
  {
#ifdef _WIN32
    return (T) GetProcAddress((HMODULE)impl, sym);
#else
    return (T) dlsym(impl, sym);
#endif
  }

  operator bool() const { return bool(impl); }

private:
  void* impl{};
};
    
}
