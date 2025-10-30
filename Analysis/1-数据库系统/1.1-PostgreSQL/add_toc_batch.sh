#!/bin/bash
#
# PostgreSQL文档批量格式化脚本
# 功能：为标题添加序号并生成目录
#
# 使用方法：
#   bash add_toc_batch.sh <目录或文件>
#

# 处理单个文件
process_file() {
    local file="$1"
    echo "处理: $file"
    
    # 备份原文件
    cp "$file" "${file}.backup"
    
    # 使用awk处理
    awk '
    BEGIN {
        h2_count = 0
        h3_count = 0
        h4_count = 0
        in_frontmatter = 0
        skip_toc = 0
    }
    
    # 跳过已有的目录部分
    /^## 目录/ {
        skip_toc = 1
        next
    }
    
    # 当遇到下一个H2时，停止跳过
    /^## [^目]/ && skip_toc {
        skip_toc = 0
    }
    
    skip_toc { next }
    
    # 处理H2标题
    /^## / {
        title = substr($0, 4)
        # 移除emoji和特殊符号
        gsub(/[🎯📐🚀📁💾🔧🎨🐳📊🔌🧪📖⚡🔧📊🎉]/, "", title)
        title = gensub(/^[[:space:]]*/, "", 1, title)
        
        if (title !~ /^[0-9]+\./ && title !~ /目录|Table of Contents/) {
            h2_count++
            h3_count = 0
            h4_count = 0
            print "## " h2_count ". " title
            next
        }
    }
    
    # 处理H3标题
    /^### / {
        title = substr($0, 5)
        title = gensub(/^[[:space:]]*/, "", 1, title)
        
        if (title !~ /^[0-9]+\.[0-9]+/ && h2_count > 0) {
            h3_count++
            h4_count = 0
            print "### " h2_count "." h3_count " " title
            next
        }
    }
    
    # 处理H4标题
    /^#### / {
        title = substr($0, 6)
        title = gensub(/^[[:space:]]*/, "", 1, title)
        
        if (title !~ /^[0-9]+\.[0-9]+\.[0-9]+/ && h2_count > 0 && h3_count > 0) {
            h4_count++
            print "#### " h2_count "." h3_count "." h4_count " " title
            next
        }
    }
    
    # 保留其他行
    { print }
    
    ' "$file" > "${file}.tmp"
    
    # 生成目录
    echo "生成目录..."
    {
        # 读取H1标题
        grep "^# " "${file}.tmp" | head -1
        echo ""
        echo "## 目录"
        echo ""
        
        # 生成目录项
        grep "^## [0-9]" "${file}.tmp" | while IFS= read -r line; do
            if echo "$line" | grep -q "^## [0-9]\+\."; then
                num=$(echo "$line" | sed 's/^## \([0-9]\+\)\..*/\1/')
                title=$(echo "$line" | sed 's/^## [0-9]\+\. //')
                anchor=$(echo "$num-$title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9\-\u4e00-\u9fa5]//g')
                echo "- [$num. $title](#$anchor)"
                
                # 添加H3子项
                awk "/^## $num\. /,/^## [0-9]/ {if (/^### $num\.[0-9]/) print}" "${file}.tmp" | while IFS= read -r h3line; do
                    if [ -n "$h3line" ]; then
                        h3num=$(echo "$h3line" | sed 's/^### \([0-9]\+\.[0-9]\+\) .*/\1/')
                        h3title=$(echo "$h3line" | sed 's/^### [0-9]\+\.[0-9]\+ //')
                        h3anchor=$(echo "$h3num-$h3title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9\-\u4e00-\u9fa5]//g')
                        echo "  - [$h3num $h3title](#$h3anchor)"
                    fi
                done
            fi
        done
        
        echo ""
        echo "---"
        echo ""
        
        # 添加正文（跳过旧的H1）
        tail -n +2 "${file}.tmp"
        
    } > "${file}.final"
    
    mv "${file}.final" "$file"
    rm "${file}.tmp"
    
    echo "✅ 完成: $file"
}

# 主程序
main() {
    if [ $# -eq 0 ]; then
        echo "用法: $0 <目录或文件路径>"
        echo ""
        echo "示例:"
        echo "  $0 06-实战案例/*.md"
        echo "  $0 06-实战案例/"
        exit 1
    fi
    
    for arg in "$@"; do
        if [ -f "$arg" ]; then
            if [[ "$arg" == *.md ]]; then
                process_file "$arg"
            fi
        elif [ -d "$arg" ]; then
            for file in "$arg"/*.md; do
                if [ -f "$file" ]; then
                    process_file "$file"
                fi
            done
        fi
    done
    
    echo ""
    echo "===================="
    echo "批量处理完成！"
    echo "===================="
    echo ""
    echo "注意："
    echo "- 原文件已备份为 .backup"
    echo "- 如需恢复：mv file.md.backup file.md"
}

main "$@"

