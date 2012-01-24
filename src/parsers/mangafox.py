#!/usr/bin/env python

####################

import re
import string

#####################

from parsers.base import SiteParserBase
from util import fixFormatting, getSourceCode

#####################

class MangaFox(SiteParserBase):
	re_getSeries = re.compile('a href="http://www.mangafox.com/manga/([^/]*)/[^"]*?" class=[^>]*>([^<]*)</a>')
	#re_getSeries = re.compile('a href="/manga/([^/]*)/[^"]*?" class=[^>]*>([^<]*)</a>')
	#re_getChapters = re.compile('"(.*?Ch.[\d.]*)[^"]*","([^"]*)"')
	re_getImage = re.compile('"><img src="([^"]*)"')
	re_getMaxPages = re.compile('var total_pages=([^;]*?);')
	
	def fixFormatting(self, s):
		
		for i in string.punctuation:
			if(i != '-'):
				s = s.replace(i, '')
			else: 
				s = s.replace(i, " ")
		
		p = re.compile( '\s+')
		s = p.sub( ' ', s )
		
		s = s.lower().strip().replace(' ', '_')
		return s
		
	def parseSite(self):
		"""
		Parses list of chapters and URLs associated with each one for the given manga and site.
		"""
		
		print('Beginning MangaFox check: %s' % self.manga)

		# jump straight to expected URL and test if manga removed
		url = 'http://www.mangafox.com/manga/%s/' % self.fixFormatting( self.manga )
		if self.verbose_FLAG:
			print(url)
		source = getSourceCode(url)
		if('it is not available in Manga Fox.' in source):
			raise self.MangaNotFound('It has been removed.')
		
		# do a 'begins-with' search, then a 'contains' search
		url = 'http://www.mangafox.com/search.php?name_method=bw&name=%s' % '+'.join(self.manga.split())
		if self.verbose_FLAG:
			print(url)
		try:
			source = getSourceCode(url)
			seriesResults = MangaFox.re_getSeries.findall(source)
			if (0 == len(seriesResults) ):
				url = 'http://www.mangafox.com/search.php?name=%s' % '+'.join(self.manga.split())
				if self.verbose_FLAG:
					print(url)
				source = getSourceCode(url)
				seriesResults = MangaFox.re_getSeries.findall(source)
				
		# 0 results
		except AttributeError:
			raise self.MangaNotFound('It doesn\'t exist, or cannot be resolved by autocorrect.')
		else:	
			keyword = self.selectFromResults(seriesResults)
			if self.verbose_FLAG:
				print ("Keyword: %s" % keyword)
			url = 'http://www.mangafox.com/manga/%s/' % keyword
			source = getSourceCode(url)
			# other check for manga removal if our initial guess for the name was wrong
			if('it is not available in Manga Fox.' in source):
				raise self.MangaNotFound('It has been removed.')
		
			# that's nice of them
			#url = 'http://www.mangafox.com/cache/manga/%s/chapters.js' % keyword
			#source = getSourceCode(url)
		
			# chapters is a 2-tuple
			# chapters[0] contains the chapter URL
			# chapters[1] contains the chapter title
			
			# can't pre-compile this because relies on class name
			re_getChapters = re.compile('a href="http://www.mangafox.com/manga/%s/(v[\d]+)/(c[\d]+)/[^"]*?" title' % keyword)
			self.chapters = re_getChapters.findall(source)
			self.chapters.reverse()
			
			for i in range(0, len(self.chapters)):
				#print("%s %s" % (self.chapters[i][0], self.chapters[i][1]))
				self.chapters[i] = ('http://www.mangafox.com/manga/%s/%s/%s' % (keyword, self.chapters[i][0], self.chapters[i][1]), self.chapters[i][0] + "." + self.chapters[i][1])
				print('(%i) %s' % (i + 1, self.chapters[i][1]))

			# which ones do we want?
			self.chapters_to_download = self.selectChapters(self.chapters)

	def downloadChapter(self, downloadThread, max_pages, url, manga_chapter_prefix, current_chapter):
		for page in range(1, max_pages + 1):
			if (self.verbose_FLAG):
				print(self.chapters[current_chapter][1] + ' | ' + 'Page %i / %i' % (page, max_pages))

			pageUrl = '%s/%i.html' % (url, page)
			self.downloadImage(downloadThread, page, pageUrl, manga_chapter_prefix)
