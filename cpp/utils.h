#pragma once

#include <stdexcept>
#include <vector>
#include <chrono>
#include <memory>
#include <fstream>
#include <iomanip>
#include <string>
#include <map>
#include <utility>

#include "BaseQuery.h"

struct BenchmarkParameters {
    enum RunMode {
        Test,
        Param,
        File
    };

    std::string CsvPath;
    std::string ParamsPath;
    std::string RunIndex;
    std::string Tool;
    std::string ChangeSet;
    int Query = -1;
    RunMode Mode = Test;
    char const *const *QueryParams = nullptr;
    std::string QueryParamsFilePath;
    int QueryParamsNum = 0;
    int ThreadsNum = 0;
};

BenchmarkParameters parse_benchmark_params(int argc, char *argv[]);

extern int GlobalNThreads;

void report_load(BenchmarkParameters const &parameters, std::chrono::nanoseconds runtime);

void report_result(BaseQuery const &query, BenchmarkParameters const &parameters, std::chrono::nanoseconds runtime,
                   std::tuple<std::string, std::string> const &result_tuple);

// https://stackoverflow.com/a/26351760
template<typename V, typename... T>
constexpr auto array_of(T &&... t)
-> std::array<V, sizeof...(T)> {
    return {{std::forward<T>(t)...}};
}

// https://stackoverflow.com/a/36585702
inline std::string const &to_string(std::string const &str) {
    return str;
}

// https://en.cppreference.com/w/cpp/utility/integer_sequence
template<typename... ParameterT, typename T, T... Ints>
std::map<std::string, std::string> getQueryParamsMapImpl(std::tuple<ParameterT...> const &query_params,
                                                         std::array<std::string, sizeof...(ParameterT)> parameter_names,
                                                         std::integer_sequence<T, Ints...>) {
    // using std::to_string or to_string
    using namespace std;

    std::map<std::string, std::string> paramsMap;
    ((paramsMap.emplace(std::get<Ints>(parameter_names), to_string(std::get<Ints>(query_params)))), ...);
    return paramsMap;
}

template<typename... ParameterT>
std::map<std::string, std::string> getQueryParamsMap(std::tuple<ParameterT...> const &query_params,
                                                     std::array<std::string, sizeof...(ParameterT)> parameter_names) {
    return getQueryParamsMapImpl(query_params, parameter_names, std::make_index_sequence<sizeof...(ParameterT)>{});
}

inline char const CSV_SEPARATOR = ',';
inline char const *CSV_SEPARATOR_STR = ",";

inline const char *TimestampFormat = "%Y-%m-%d %H:%M:%S";
inline const char *DateFormat = "%Y-%m-%d";

time_t parseTimestamp(const char *timestamp_str, const char *timestamp_format);

std::string timestampToString(std::time_t timestamp, const char *timestamp_format);

/// Returns a comparator which compares T instances (using comparator comp) after applying operator op.
///
/// Default comparator: op(lhs) &lt; op(rhs).
///
/// Recommendation: if more values should be compared, transform them into a std::tuple.
/// Change comp to std::greater&lt;&gt;{} for decreasing order, or negate corresponding elements in the tuple.
///
/// \tparam UnaryOp type of op
/// \tparam ComparatorForTransformed type of comp
/// \param op an operator which transforms T instances to TransformedT instances
/// \param comp comparator used for TransformedT (default: std::less&lt;&gt;)
/// \return a comparator for T instances
template<typename UnaryOp, typename ComparatorForTransformed = std::less<>>
auto transformComparator(const UnaryOp &op, ComparatorForTransformed comp = ComparatorForTransformed{}) {
    return [&, comp = std::move(comp)](const auto &lhs, const auto &rhs) {
        return comp(op(lhs), op(rhs));
    };
}

class Printer {
    std::ofstream m_output;
    const std::string m_prefix;
    const std::string m_postfix;
    const std::string m_separator;
public:
    Printer(const std::string &filePath,
            std::string prefix = "",
            std::string postfix = "",
            std::string separator = CSV_SEPARATOR_STR)
            : m_output(), m_prefix(std::move(prefix)), m_postfix(std::move(postfix)),
              m_separator(std::move(separator)) {
        m_output.exceptions(std::ifstream::failbit | std::ifstream::badbit);
        m_output.open(filePath);
    }

    template<typename Arg, typename... Args>
    void print(Arg &&arg, Args &&... args) {
        m_output << m_prefix << std::forward<Arg>(arg);
        ((m_output << m_separator << std::forward<Args>(args)), ...);
        m_output << m_postfix << std::endl;
    }
};
