//! \file
/*
**  Copyright (C) - Triton
**
**  This program is under the terms of the Apache License 2.0.
*/

#ifndef TRITON_Z3TOTRITONAST_H
#define TRITON_Z3TOTRITONAST_H

#include <z3++.h>

#include <triton/ast.hpp>
#include <triton/dllexport.hpp>
#include <triton/tritonTypes.hpp>



//! The Triton namespace
namespace triton {
/*!
 *  \addtogroup triton
 *  @{
 */

  //! The AST namespace
  namespace ast {
  /*!
   *  \ingroup triton
   *  \addtogroup ast
   *  @{
   */

    //! \class Z3ToTriton
    /*! \brief Converts a Z3's AST to a Triton's AST. */
    class Z3ToTriton {
      private:
        //! The Triton's AST context
        triton::ast::SharedAstContext astCtxt;

      public:
        //! Constructor.
        TRITON_EXPORT Z3ToTriton(const triton::ast::SharedAstContext& ctxt);

        //! Converts to Triton's AST
        TRITON_EXPORT triton::ast::SharedAbstractNode convert(const z3::expr& expr);
    };

  /*! @} End of ast namespace */
  };
/*! @} End of triton namespace */
};

#endif /* TRITON_Z3TOTRITONAST_H */
