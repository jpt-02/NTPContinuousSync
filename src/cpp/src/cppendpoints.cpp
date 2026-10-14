/*
Implementation file for cppendpoints

Contains cpp versions of each python endpoint
*/

#include "offset_anchor.hpp"
#include <atomic>
#include <array>
#include <rcu>

class CppSimple {
    /*
    TODO: finish writing this 

    C++ implementation of the Simlpe endpoint. Uses RCU to update the offset anchor. 
    */
    private:
        
        OffsetAnchor anchor_{create_offset_anchor(1,0)};

        alignas(64) std::atomic<uint64_t> seq_{0}; // sequence counter. Even = clean state, odd = writer is mid-update
    

    public:
        // handle updates from Python side
        void update(const OffsetAnchor& new_anchor) {
            uint64_t s = seq_.load(std::memory_order_relaxed); // load the sequence counter
            seq_.store(s+1, std::memory_order_relaxed); // store an odd number in the sequence counter
            std::atomic_thread_fence(std::memory_order_release);
            // Fence Rule: all preceding memory writes are visible before any subsequent memory operations can be seen by other threads
            anchor_ = new_anchor;
            // Fence Rule: all preceding memory writes are visible before any subsequent memory operations can be seen by other threads
            seq_.store(s+2, std::memory_order_release); // sets sequence to even. ensures all memory writes are finished before doing this operation

        }
}