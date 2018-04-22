#ifndef ZENCAD_UTIL_H
#define ZENCAD_UTIL_H

template<typename T>
std::ostream& binary_write(std::ostream& stream, const T& value){
    return stream.write(reinterpret_cast<const char*>(&value), sizeof(T));
}

template<typename T>
std::istream & binary_read(std::istream& stream, T& value){
    return stream.read(reinterpret_cast<char*>(&value), sizeof(T));
}

static inline std::ostream& binary_string_write(std::ostream& stream, const std::string& str){
    binary_write(stream, str.size());
    stream.write(str.data(), str.size());
    return stream;
}

static inline std::istream & binary_string_read(std::istream& stream, std::string& value){
    size_t sz;
    binary_read(stream, sz);
    value.resize(sz);
    stream.read(&value[0], sz);

    //return stream.read(reinterpret_cast<char*>(&value), sizeof(T));
}


#endif