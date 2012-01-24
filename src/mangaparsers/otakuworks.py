#!/usr/bin/env python

####################

import re

#####################

from mangaparsers.parser import Parser
from util import fixFormatting, getSourceCode

#####################

class OtakuWorks(Parser):
	
	re_getMangas = re.compile('a href="([^"]*?)"[^>]*?>([^<]*?) \(Manga\)')
	re_getImage = re.compile('img src="(http://static.otakuworks.net/viewer/[^"]*)"')
	re_getMaxPages = re.compile('<strong>(\d*)</strong>')
	
	def parseSite(self):
		print('Beginning OtakuWorks check: %s' % self.manga)
		url = 'http://www.otakuworks.com/search/%s' % '+'.join(self.manga.split())

		source = getSourceCode(url)
		
		info = OtakuWorks.re_getMangas.findall(source)
		
		# we either have 0 search results or we have already been redirected to the manga homepage
		if len(info) != 0:
			keyword = self.selectFromResults(info)
			source = getSourceCode(keyword)
	
		if(source.find('has been licensed and as per request all releases under it have been removed.') != -1):
			raise self.MangaNotFound('It has been removed.')
		
		# can't pre-compile this because relies on class name
		self.chapters = re.compile('a href="([^>]*%s[^>]*)">([^<]*#[^<]*)</a>' % '-'.join(fixFormatting(self.manga).replace('_', ' ').split())).findall(source)
		self.chapters.reverse()

		lowerRange = 0
		
		for i in range(0, len(self.chapters)):
			self.chapters[i] = ('http://www.otakuworks.com' + self.chapters[i][0] + '/read', self.chapters[i][1])
			if (not self.auto):
				print('(%i) %s' % (i + 1, self.chapters[i][1]))
			else:
				if (self.lastDownloaded == self.chapters[i][1]):
					lowerRange = i + 1
		
		# this might need to be len(self.chapters) + 1, I'm unsure as to whether python adds +1 to i after the loop or not
		upperRange = len(self.chapters)	
	
		if (not self.auto):
			self.chapters_to_download = self.selectChapters(self.chapters)
		else:
			if ( lowerRange == upperRange):
				raise self.NoUpdates
			for i in range (lowerRange, upperRange):
				self.chapters_to_download.append(i)
		return 
		
	def downloadChapter(self, downloadThread, max_pages, url, manga_chapter_prefix, current_chapter):
		for page in range(1, max_pages + 1):
			if (self.verbose_FLAG):
				print(self.chapters[current_chapter][1] + ' | ' + 'Page %i / %i' % (page, max_pages))
					
			pageUrl = '%s/%i' % (url, page)
			self.downloadImage(downloadThread, page, pageUrl, manga_chapter_prefix)
