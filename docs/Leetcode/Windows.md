!!! note "历史参考资料"
    本文继承自[上游笔记库](https://github.com/zwygit2025/My-CS-Notebook/blob/a94d023/docs/Leetcode/Windows.md)，原有叙述与署名属于对应作者。涉及当前框架和接口时，请结合官方文档核验。

# 滑动窗口

## 0003. 无重复字符的最长子串
> 给定一个字符串 s ，请你找出其中不含有重复字符的 最长子串 的长度。

滑动窗口的经典题目，用一个map记录每个字符出现的次数，在窗口滑动的过程中保证任何一个字符出现的次数不要大于2就可以了。

```cpp
class Solution {
public:
    int lengthOfLongestSubstring(string s) {
        // 滑动窗口的经典题目
        int left = 0, right = 0, maxl = 0;
        map<char, int> mp;
        while (right < s.size()) {
            mp[s[right]] += 1;
            while (mp[s[right]] >= 2) {
                mp[s[left]] -= 1;
                left += 1;
            }
            maxl = max(maxl, right - left + 1);
            right += 1;
        }
        return maxl;
    }
};
```