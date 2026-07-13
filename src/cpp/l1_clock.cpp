/*
Implementation file for l1_clock
Lots of comments because I'm new to C++
*/

// imports
#include "l1_clock.hpp" // include its own header file to ensure vars and funcs match
#include <cstdint> // gives us uint64_t, which is always 64 bits and can safely store large ms values
#include <atomic> // gives us std::atomic type wrapper, used to prevent race conditions for a single variable
#include <chrono> // system clocks
#include <thread> // threading
#include <new> // used for allocating memory, important for storing in l1 cache
#include <windows.h> // required for core affinity mask, timeBeginPeriod and timeEndPeriod to change refresh rate
#include <iostream> // for print statements

// Code

namespace chrono = std::chrono; // shortens import for usage in code

alignas(std::hardware_destructive_interference_size) std::atomic<uint64_t> current_ms{0};

// Private variables for thread and whether or not its running
static std::atomic<bool> running{true};
static std::thread clock_thread;
static std::atomic<bool> clock_ready{false}; // makes thread wait until clock is ready to proceed

// Definition of worker function
template <bool UseSleep> // Create a template for UseSleep so there isnt a if statement in the main loop after compilation
void update_clock_loop(bool confine_to_core) {
    /*
    TODO: write description for this function
    */
    
    // Template, change windows refresh rate to 1 ms
    if constexpr (UseSleep) { // constexpr means the if statement happens at compile time, not runtime
        auto result = timeBeginPeriod(1);
        if (result == TIMERR_NOERROR) {
            std::cout << "[Clock] Successfully changed Windows timer resolution to 1ms\n";
        } else {
            std::cout << "[Clock] Failed to change timer resolution. Code: " << result << "\n";
        }
    }

    // Handle confine_to_core
    if (confine_to_core) {
        DWORD_PTR mask = 1; // Bitmask; 1 = Core 0, 2 = Core 1, 4 = Core 2, etc.
        SetThreadAffinityMask(GetCurrentThread(), mask);
    }
    
    // Mark clock as ready
    clock_ready.store(true, std::memory_order_release); // memory order release paired with memory order acquire in the start_clock function 

    auto start_time = chrono::steady_clock::now(); // steady_clock is monotonic. No units yet, thats handled later
    while (running.load(std::memory_order_relaxed)){ // memory order relaxed = doesnt care about any other threads, just instantly does what it needs to do. Load is how you read an atomic var with thread safety.
        auto now = chrono::steady_clock::now(); // get the time right now
        auto duration = chrono::duration_cast<chrono::milliseconds>(now - start_time); // calculates duration, uses type cast to make into ms
        current_ms.store(duration.count(), std::memory_order_relaxed); // uses .count to turn C++ time point into regular integer, stores in current_ms variable with thread safety

        if constexpr (UseSleep) {
            std::this_thread::sleep_for(chrono::milliseconds(1)); // sleep for 1 ms so CPU core utilization isnt at 100% due to contant while looping
        }
    }

    // Change windows refresh rate back to normal
    if constexpr (UseSleep) {
        timeEndPeriod(1);
    }
}

// Starts the thread
void start_clock(bool confine_to_core, bool use_sleep) {
    /*
    Starts the clock in a thread.

    confine_to_core: the thread resides on a single core
    use_sleep: prevents 100% core utilization by sleeping, but requires OS to change 
        refresh rate to 1ms.

    TODO: figure out what happens if this is called multiple times without a stop
    */
    clock_ready.store(false, std::memory_order_relaxed); // reset to not ready before starting clock again
    running.store(true, std::memory_order_relaxed); // set running variable to true
    if (use_sleep) {
        clock_thread = std::thread(update_clock_loop<true>, confine_to_core);
    } else {
        clock_thread = std::thread(update_clock_loop<false>, confine_to_core);
    }
    
    while (!clock_ready.load(std::memory_order_acquire)) {
        std::this_thread::sleep_for(chrono::microseconds(100)); // stops CPU from going to 100%
    }

}

// Stops the thread
void stop_clock() {
    /*
    Stops the thread
    */
    running.store(false, std::memory_order_relaxed);
    if (clock_thread.joinable()) {
        clock_thread.join();
    }
}

uint64_t get_current_ms() {
    /*
    Returns ms since clock was started
    */
    return current_ms.load(std::memory_order_relaxed);
}