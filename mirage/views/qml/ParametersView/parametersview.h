#ifndef PARAMETERSVIEW_H
#define PARAMETERSVIEW_H

#include <QWidget>

namespace Ui {
class ParametersView;
}

class ParametersView : public QWidget
{
    Q_OBJECT

public:
    explicit ParametersView(QWidget *parent = nullptr);
    ~ParametersView();

private:
    Ui::ParametersView *ui;
};

#endif // PARAMETERSVIEW_H
