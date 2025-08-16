-- Insert a page break before each level-2 header, so chapters start on a new page
-- Works across PDF (LaTeX), EPUB (CSS page-break), and DOCX

local function pagebreak_block()
  if FORMAT:match('latex') then
    return pandoc.RawBlock('latex', '\\clearpage')
  elseif FORMAT:match('epub') or FORMAT:match('html') then
    -- epub/html: use a div with CSS page-break
    return pandoc.Div({}, pandoc.Attr('', { 'pagebreak' }))
  elseif FORMAT:match('docx') then
    return pandoc.RawBlock('openxml',
      '<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
  else
    -- Fallback: a horizontal rule as a visible separator
    return pandoc.HorizontalRule()
  end
end

function Header(el)
  -- Parts are level-1 headings (#), Chapters are level-2 headings (##)
  if el.level == 1 or el.level == 2 then
    -- Add page break before all level-1 (parts) and level-2 (chapters) headers
    return { pagebreak_block(), el }
  end
  return nil
end