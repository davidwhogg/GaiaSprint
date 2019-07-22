grep -E -o '<li><a href="http.+">' *html | awk '{ split($2,a,"\""); print(a[2]); }' > papers.log
uniq papers.log | sort | wc | awk '{print $1, "papers total" }'
rm -f papers.log