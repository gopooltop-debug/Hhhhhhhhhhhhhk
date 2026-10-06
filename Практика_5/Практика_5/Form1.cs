using System;
using System.IO;
using System.Text;
using System.Windows.Forms;

namespace Практика_5
{
    public partial class Form1 : Form
    {
        // Имя файла фигурирует в приложении постоянно, поэтому объявлено в теле формы.
        String File_name = "Noname.rtf";

        public Form1()
        {
            InitializeComponent();

            // Диалоги открытия и сохранения начинают поиск с папки «Документы».
            openFileDialog1.InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
            saveFileDialog1.InitialDirectory = openFileDialog1.InitialDirectory;

            UpdateTitle();
            UpdatePosition();
        }

        // ============================ Файл ============================

        // Создать.
        private void newToolStripMenuItem_Click(object sender, EventArgs e)
        {
            // Предварительно проверить, что есть в окне, и предложить сохранить.
            if (!AskSave())
                return;

            richTextBox1.Clear();
            File_name = "Noname.rtf";
            richTextBox1.Modified = false;
            UpdateTitle();
        }

        // Открыть файл.
        private void openToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (!AskSave())
                return;

            // Имя файла в поле ввода имени.
            openFileDialog1.FileName = File_name;
            // Показать диалог и ждать ОК.
            if (openFileDialog1.ShowDialog() == DialogResult.OK)
                LoadText(openFileDialog1.FileName);
            // Не ОК — ничего не делаем, остаётся прежний документ.
        }

        // Сохранить (быстрое сохранение).
        private void saveToolStripMenuItem_Click(object sender, EventArgs e)
        {   // Отследить первоначальное сохранение.
            if (File_name == "Noname.rtf")
                // Файл ещё ни разу не сохраняли — вызвать пункт меню «Сохранить как».
                saveAsToolStripMenuItem_Click(sender, e);
            else
                // Сохранить текст в файле.
                SaveText(File_name);
        }

        // Сохранить с именем.
        private void saveAsToolStripMenuItem_Click(object sender, EventArgs e)
        {
            // Имя файла в поле ввода имени, тип файла — как у текущего.
            saveFileDialog1.FileName = File_name;
            saveFileDialog1.FilterIndex = IsRtf(File_name) ? 1 : 2;
            // Показать диалог и ждать ОК.
            if (saveFileDialog1.ShowDialog() == DialogResult.OK)
                // Расширение диалог добавляет сам (DefaultExt = "rtf"),
                // поэтому «+ ".rtf"» к имени не дописываем, иначе получится file.rtf.rtf.
                SaveText(saveFileDialog1.FileName);
        }

        // Выход.
        private void exitToolStripMenuItem_Click(object sender, EventArgs e)
        {
            Close();   // вопрос о сохранении задаётся в Form1_FormClosing
        }

        // Окно закрывается (пункт «Выход», крестик, Alt+F4) — предложить сохранить текст.
        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (!AskSave())
                e.Cancel = true;   // нажали «Отмена» — остаёмся в редакторе
        }

        // Если текст изменён, спросить, сохранить ли его.
        // Возвращает false, если пользователь передумал (нажал «Отмена»).
        bool AskSave()
        {
            if (!richTextBox1.Modified)        // изменений нет — спрашивать не о чем
                return true;

            DialogResult answer = MessageBox.Show(
                "Сохранить изменения в файле «" + Path.GetFileName(File_name) + "»?",
                "Маленький текстовый редактор",
                MessageBoxButtons.YesNoCancel,
                MessageBoxIcon.Question);

            if (answer == DialogResult.Cancel)
                return false;
            if (answer == DialogResult.Yes)
            {
                saveToolStripMenuItem_Click(this, EventArgs.Empty);
                return !richTextBox1.Modified;  // в диалоге сохранения нажали «Отмена» — не продолжаем
            }
            return true;                        // «Нет» — продолжаем без сохранения
        }

        // .rtf — текст с форматированием, остальные файлы (.txt) — простой текст.
        static bool IsRtf(string fileName)
        {
            return Path.GetExtension(fileName).ToLower() == ".rtf";
        }

        // Загрузить файл в окно редактирования.
        void LoadText(string fileName)
        {
            try
            {
                if (IsRtf(fileName))
                    richTextBox1.LoadFile(fileName, RichTextBoxStreamType.RichText);
                else
                    // LoadFile(..., PlainText) читает файл в кодировке ANSI, и русский текст
                    // из UTF-8 файла превратился бы в «кракозябры». File.ReadAllText понимает UTF-8.
                    richTextBox1.Text = File.ReadAllText(fileName);

                File_name = fileName;
                richTextBox1.Modified = false;
            }
            catch (Exception ex)
            {
                MessageBox.Show("Не удалось открыть файл:\n" + ex.Message, "Ошибка",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            UpdateTitle();
        }

        // Записать текст из окна редактирования в файл.
        void SaveText(string fileName)
        {
            try
            {
                if (IsRtf(fileName))
                    richTextBox1.SaveFile(fileName, RichTextBoxStreamType.RichText);
                else
                    File.WriteAllText(fileName, richTextBox1.Text, Encoding.UTF8);

                File_name = fileName;
                richTextBox1.Modified = false;
            }
            catch (Exception ex)
            {
                MessageBox.Show("Не удалось сохранить файл:\n" + ex.Message, "Ошибка",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            UpdateTitle();
        }

        // ============================ Правка ============================

        private void undoToolStripMenuItem_Click(object sender, EventArgs e)
        {
            richTextBox1.Undo();
        }

        private void redoToolStripMenuItem_Click(object sender, EventArgs e)
        {
            richTextBox1.Redo();
        }

        private void cutToolStripMenuItem_Click(object sender, EventArgs e)
        {
            richTextBox1.Cut();
        }

        private void copyToolStripMenuItem_Click(object sender, EventArgs e)
        {
            richTextBox1.Copy();
        }

        private void pasteToolStripMenuItem_Click(object sender, EventArgs e)
        {
            // Сначала проверяем, есть ли в буфере обмена данные нужного формата.
            DataFormats.Format rtfFormat = DataFormats.GetFormat(DataFormats.Rtf);
            DataFormats.Format textFormat = DataFormats.GetFormat(DataFormats.UnicodeText);

            if (Clipboard.ContainsData(rtfFormat.Name))
                richTextBox1.Paste(rtfFormat);      // текст с форматированием
            else if (Clipboard.ContainsData(textFormat.Name))
                richTextBox1.Paste(textFormat);     // простой текст
        }

        private void selectAllToolStripMenuItem_Click(object sender, EventArgs e)
        {
            richTextBox1.SelectAll();
        }

        // ============================ Справка ============================

        private void aboutToolStripMenuItem_Click(object sender, EventArgs e)
        {
            MessageBox.Show(
                "Маленький текстовый редактор\n\n" +
                "Практика 5: SDI-интерфейс настольного приложения —\n" +
                "меню, панель инструментов, строка состояния.",
                "О программе", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        // ===================== Панель инструментов =====================

        // Обработчики событий кнопок инструментальной панели дублируют пункты меню.
        // Обработчик один на всю панель: номер кнопки (с нуля, разделители тоже
        // считаются) определяет выполняемое действие.
        private void toolStrip1_ItemClicked(object sender, ToolStripItemClickedEventArgs e)
        {
            switch (toolStrip1.Items.IndexOf(e.ClickedItem))
            {
                case 0: { /*Создать*/    newToolStripMenuItem_Click(sender, e); break; }
                case 1: { /*Открыть*/    openToolStripMenuItem_Click(sender, e); break; }
                case 2: { /*Сохранить*/  saveToolStripMenuItem_Click(sender, e); break; }
                // 3 — разделитель
                case 4: { /*Вырезать*/   cutToolStripMenuItem_Click(sender, e); break; }
                case 5: { /*Копировать*/ copyToolStripMenuItem_Click(sender, e); break; }
                case 6: { /*Вставить*/   pasteToolStripMenuItem_Click(sender, e); break; }
                // 7 — разделитель
                case 8: { /*Справка*/    aboutToolStripMenuItem_Click(sender, e); break; }
            }
        }

        // ======================= Строка состояния =======================

        // Заголовок окна и строка состояния: имя файла и признак несохранённых изменений.
        void UpdateTitle()
        {
            Text = Path.GetFileName(File_name) + (richTextBox1.Modified ? "*" : "") +
                   " — Маленький текстовый редактор";
            fileNameStatusLabel.Text = File_name;
            modifiedStatusLabel.Text = richTextBox1.Modified ? "Изменён" : "";
        }

        // Позиция курсора и количество символов.
        void UpdatePosition()
        {
            int pos = richTextBox1.SelectionStart;
            int line = richTextBox1.GetLineFromCharIndex(pos);
            int column = pos - richTextBox1.GetFirstCharIndexFromLine(line);

            positionStatusLabel.Text = "Стр " + (line + 1) + ", стлб " + (column + 1);
            lengthStatusLabel.Text = "Символов: " + richTextBox1.TextLength;
        }

        private void richTextBox1_TextChanged(object sender, EventArgs e)
        {
            UpdateTitle();
            UpdatePosition();
        }

        private void richTextBox1_SelectionChanged(object sender, EventArgs e)
        {
            UpdatePosition();
        }
    }
}
