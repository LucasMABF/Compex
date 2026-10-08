"""Monta o prompt a partir de (autor, proposta). O texto da proposta
é sempre o mesmo; só a autoria muda — é isso que garante o desenho
within-item (comparação pareada)."""


def montar_prompt(proposta_texto, autor_nome, template_autor, template_neutro):
    """Retorna o prompt final.
    autor_nome=None  -> condição de controle (sem autoria)."""
    if autor_nome is None:
        return template_neutro.format(proposta=proposta_texto)
    return template_autor.format(autor=autor_nome, proposta=proposta_texto)
