#!/usr/bin/env ruby
# frozen_string_literal: true
#
# Front matter integrity gate for every post in _posts/.
#
# Added 2026-10-22 after five posts shipped with malformed YAML frontmatter.
# Ruby's YAML parser is the same one Jekyll uses, so this is authoritative —
# a Python regex checker cannot see a YAML-level parse failure.
#
# Checks, per post:
#   1. Front matter block exists and parses as YAML.
#   2. Required keys present: title, date, layout, description, hero_image.
#   3. The title is not a truncated fragment of its own description.
#   4. Filename date prefix matches the front matter date.
#   5. The permalink derived from (date, filename slug) is unique repo-wide.
#   6. No stray markdown emphasis leaked into the title.
#
# Usage:  ruby _tests/check_front_matter.rb
# Exit code 0 = clean, 1 = failures found.

require "yaml"
require "date"

POSTS_DIR = File.join(__dir__, "..", "_posts")
REQUIRED_KEYS = %w[title date layout description hero_image].freeze

def slugify(text)
  text.to_s.downcase.gsub(/[^a-z0-9]/, "-").gsub(/-+/, "-").gsub(/\A-|-\z/, "")
end

def front_matter(path)
  raw = File.read(path, encoding: "UTF-8")
  m = raw.match(/\A---\s*\n(.*?)\n---\s*\n/m)
  return [nil, nil] unless m
  [raw, m[1]]
end

failures = []
urls = Hash.new { |h, k| h[k] = [] }

posts = Dir.glob(File.join(POSTS_DIR, "*.md")).sort
puts "• checking #{posts.size} posts"

posts.each do |path|
  name = File.basename(path)
  _raw, block = front_matter(path)
  unless block
    failures << "#{name}: no front matter block"
    next
  end

  data = begin
    YAML.safe_load(block, permitted_classes: [Date, Time], aliases: true)
  rescue StandardError => e
    failures << "#{name}: YAML parse error — #{e.message.lines.first.to_s.strip}"
    nil
  end
  next unless data.is_a?(Hash)

  REQUIRED_KEYS.each do |key|
    value = data[key]
    failures << "#{name}: missing #{key}" if value.nil? || value.to_s.strip.empty?
  end

  title = data["title"].to_s
  description = data["description"].to_s

  # 3. Truncated title: the daily-post family embeds the full headline at the
  #    start of the description. If the title is a strict prefix of that
  #    headline, the title was cut off mid-sentence.
  if title.length > 20 && description.length > title.length + 5
    bare = title.sub(/\A\[[A-Z]{2}\]\s*/, "")
    head = description.split(/\s+[—–-]\s+/).first.to_s
    if bare.length > 20 && head.start_with?(bare) && head.length > bare.length
      failures << "#{name}: truncated title — #{bare.inspect} is cut from #{head.inspect}"
    end
  end

  # 6. Markdown emphasis leaking into the front matter title.
  failures << "#{name}: stray '**' in title" if title.include?("**")

  # 6b. Posts must render through the post layout, not a raw/static page.
  layout = data["layout"].to_s
  failures << "#{name}: layout is #{layout.inspect}, expected \"post\"" if layout != "post" 

  # 4. Filename date prefix vs front matter date.
  stem = File.basename(path, ".md")
  filename_date = stem[/\A(\d{4}-\d{2}-\d{2})-/, 1]
  if filename_date
    fm_date = data["date"]
    fm_str = fm_date.respond_to?(:strftime) ? fm_date.strftime("%Y-%m-%d") : fm_date.to_s[0, 10]
    failures << "#{name}: filename date #{filename_date} != front matter date #{fm_str}" if fm_str != filename_date
  end

  # 5. Permalink uniqueness.
  fm_date = data["date"]
  date_str = fm_date.respond_to?(:strftime) ? fm_date.strftime("%Y-%m-%d") : fm_date.to_s[0, 10]
  if date_str.length == 10
    slug = slugify(stem.sub(/\A\d{4}-\d{2}-\d{2}-/, ""))
    urls["/blog/#{date_str[0, 4]}/#{date_str[5, 2]}/#{date_str[8, 2]}/#{slug}/"] << name
  end
end

urls.each do |url, names|
  next if names.size < 2
  failures << "duplicate permalink #{url} — #{names.join(', ')}"
end

if failures.empty?
  puts "  PASS: all #{posts.size} posts have valid, unique front matter"
  exit 0
end

puts "  FAIL: #{failures.size} front matter problem(s):"
failures.first(25).each { |f| puts "    #{f}" }
puts "    ... and #{failures.size - 25} more" if failures.size > 25
exit 1
