# -
小红书、微博、大众点评/京东爬虫

weibo.py 替换成你的cookie就可以了，然后修改你想修改的关键字和时间范围就可以

xiaohongshu.py需要把seleium的链接替换你的链接，然后修改关键词就可以，需要注意及时扫码登陆。如果爬的评论不多可以把 scroll_times = 80  # 向下滚动的次数这一行修改少点，5-10左右就可以，提高爬取的速度。然后我的只爬一级评论，二级评论没有爬。

dazhongdianping .ipynb有两个，一个是爬店铺信息的，这个简单，只要修改cookie和网页就可以，注意修改网页把后面的p1的1删掉，因为要多页爬取；

第二个是爬评价，这个和上面的一样，但是大众点评对评价监控十分严格，大搞爬50-60页评价就锁账号，就要重新登陆了，需要注意。

2.15  添加了京东的爬取的代码，和小红书一样修改Driver路径就可以了，需要先要扫码登陆。想搜其他商品修改keyword=后面的就可以了，页数也要根据你的修改下，京东比淘宝稳定（淘宝过年更新后封的挺严重的，一快就封了）如果爬的遇到爬不到，说明被京东封了，time.sleep(10 + (page % 3))这里加点时间应该就没问题了。
