#include <iostream>
#include <functional>

using std::cout;
using std::endl;

int main(int argc, char *argv[]) {
    int sum = []() { return (1 + 3); }();
    int (*add)(int, int) = [](int a, int b) -> int {
        return (a + b);
    };
    cout << "sum = " << sum << endl;

    cout << "sum of 5 + 6 = " << add(5, 6) << endl;

    return 0;
}
